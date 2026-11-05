import hashlib
import json
import time
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import case, delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .models import Comment, ContentAudit, ContentRateBucket, ModerationJob, Post, PUBLIC_VISIBILITY


def privileged(user):
    return user.role in {"admin", "moderator"}


def visible_post(post, user):
    return post is not None and (post.author_id == user.id or privileged(user) or post.visibility_status in PUBLIC_VISIBILITY)


def visible_comment(db, comment, user):
    if comment is None:
        return False
    if comment.author_id == user.id or privileged(user):
        return True
    if comment.visibility_status not in PUBLIC_VISIBILITY:
        return False
    post = db.get(Post, comment.post_id)
    if post is None or post.visibility_status not in PUBLIC_VISIBILITY:
        return False
    seen = {comment.id}
    parent_id = comment.parent_id
    while parent_id:
        if parent_id in seen or len(seen) >= 33:
            return False
        seen.add(parent_id)
        parent = db.get(Comment, parent_id)
        if parent is None or parent.post_id != comment.post_id or parent.visibility_status not in PUBLIC_VISIBILITY:
            return False
        parent_id = parent.parent_id
    return True


def output(row, user):
    private = row.author_id == user.id or privileged(user)
    deleted = row.visibility_status == "DELETED_BY_AUTHOR"
    result = {
        "id": row.id, "author_id": row.author_id, "body": None if deleted else row.body,
        "content_revision": row.content_revision, "decision_version": row.decision_version,
        "visibility_status": row.visibility_status if private else "PUBLISHED",
        "review_status": row.review_status if private and not deleted else None,
        "risk_tier": row.risk_tier if private and not deleted else None,
        "created_at": datetime.fromtimestamp(row.created_at, tz=timezone.utc),
        "updated_at": datetime.fromtimestamp(row.updated_at, tz=timezone.utc),
    }
    if isinstance(row, Comment):
        result.update(post_id=row.post_id, parent_id=row.parent_id)
    return result


def fingerprint(body, post_id=None, parent_id=None):
    raw = json.dumps({"body": body, "post_id": post_id, "parent_id": parent_id}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def prior_create(db, model, user, key, digest):
    row = db.scalar(select(model).where(model.author_id == user.id, model.create_key == key))
    if row and row.request_hash != digest:
        raise HTTPException(409, "Idempotency key already used with different content")
    return row


def rate_limit(db, settings, user):
    now = int(time.time())
    width = settings.content_rate_window_seconds
    window = now // width * width
    key = hashlib.sha256(f"content:{user.id}".encode()).hexdigest()
    db.execute(delete(ContentRateBucket).where(ContentRateBucket.window_start < window - width))
    insert = sqlite_insert if db.bind.dialect.name == "sqlite" else pg_insert
    statement = insert(ContentRateBucket).values(key_hash=key, window_start=window, count=1)
    statement = statement.on_conflict_do_update(index_elements=[ContentRateBucket.key_hash], set_={
        "count": case((ContentRateBucket.window_start == window, ContentRateBucket.count + 1), else_=1),
        "window_start": window,
    }).returning(ContentRateBucket.count)
    count = db.execute(statement).scalar_one()
    db.commit()  # Only the limiter changed; preserve throttling even if the content request fails.
    if count > settings.content_rate_limit:
        raise HTTPException(429, "Too many content mutations", headers={"Retry-After": str(window + width - now)})
    if db.bind.dialect.name == "sqlite":
        db.connection(execution_options={"sqlite_immediate": True})


def audit(db, row, user, event, before=None, reason=None, details=None):
    db.add(ContentAudit(entity_type="comment" if isinstance(row, Comment) else "post", entity_id=row.id,
        content_revision=row.content_revision, decision_version=row.decision_version,
        actor_id=user.id, actor_role=user.role, event=event, reason=reason or event,
        before_visibility=before, after_visibility=row.visibility_status, policy_version=row.policy_version,
        details_json=json.dumps(details, ensure_ascii=False) if details is not None else None))


def enqueue(db, row):
    db.add(ModerationJob(entity_type="comment" if isinstance(row, Comment) else "post", entity_id=row.id,
        content_revision=row.content_revision, expected_decision_version=row.decision_version,
        policy_version=None, status="QUEUED"))


def invalidate_jobs(db, row):
    db.execute(update(ModerationJob).where(
        ModerationJob.entity_type == ("comment" if isinstance(row, Comment) else "post"),
        ModerationJob.entity_id == row.id,
        ModerationJob.status.in_(["QUEUED", "PROCESSING", "RETRY_WAIT"]),
    ).values(status="SUCCEEDED", outcome="STALE_IGNORED", claim_token=None, lease_until=None, request_json=None))


def require_versions(row, payload):
    if row.content_revision != payload.expected_revision or row.decision_version != payload.expected_decision_version:
        raise HTTPException(409, "Content revision or decision version changed")


def mutate(db, row, user, payload, *, deleting=False):
    own = row.author_id == user.id
    if not own and (not deleting or user.role != "admin"):
        raise HTTPException(403, "Only the author can edit; only author/admin can remove")
    require_versions(row, payload)
    if row.visibility_status == "DELETED_BY_AUTHOR":
        if deleting and own:
            return row
        raise HTTPException(409, "Deleted content cannot be edited or restored")
    before = row.visibility_status
    if deleting and not own and not payload.reason:
        raise HTTPException(422, "Admin removal requires a reason")
    if not own:
        from .review_store import check_claim, open_appeal
        check_claim(db, row, user)
        if open_appeal(db, row):
            raise HTTPException(409, "Resolve the open appeal explicitly")
    invalidate_jobs(db, row)
    from .review_store import close_work
    close_work(db, row, "AUTHOR_DELETED" if deleting and own else "SUPERSEDED" if not deleting else "MANUAL_HIDE", user.id)
    row.decision_version += 1
    row.updated_at = int(time.time())
    if deleting:
        row.visibility_status = "DELETED_BY_AUTHOR" if own else "HIDDEN"
        row.review_status = "RESOLVED" if own else "REJECTED"
        event = "AUTHOR_DELETE" if own else "ADMIN_HIDE"
    else:
        row.body = payload.body
        row.content_revision += 1
        row.visibility_status, row.review_status, row.risk_tier = "PENDING_MODERATION", "QUEUED", "UNKNOWN"
        row.policy_version = None
        event = "EDIT"
        enqueue(db, row)
    audit(db, row, user, event, before, payload.reason if deleting else None)
    db.commit()
    return row


def blocked_comments(post_id):
    blocked = select(Comment.id).where(Comment.post_id == post_id,
        Comment.visibility_status.not_in(PUBLIC_VISIBILITY)).cte("blocked_comments", recursive=True)
    # UNION deduplicates ids, so even a corrupt cyclic parent graph terminates.
    return blocked.union(select(Comment.id).join(blocked, Comment.parent_id == blocked.c.id))
