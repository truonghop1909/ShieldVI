"""Review helpers; mutations run under the content lock, never in AI DB."""
import json
import time

from fastapi import HTTPException
from sqlalchemy import select, update

from .content_store import audit, output
from .models import Appeal, Comment, ContentAudit, ContentReport, ModerationJob, ModerationResult, Post, ReviewClaim


def kind_of(row):
    return "comment" if isinstance(row, Comment) else "post"


def matching(model, row):
    return (model.entity_type == kind_of(row), model.entity_id == row.id,
            model.content_revision == row.content_revision)


def open_appeal(db, row):
    return db.scalar(select(Appeal).where(*matching(Appeal, row), Appeal.status == "OPEN"))


def appeal_output(item, staff=False):
    result = {key: getattr(item, key) for key in ("id", "content_revision", "status", "reason", "outcome",
        "resolution_reason", "created_at", "resolved_at", "appealed_decision_version")}
    if staff:
        result.update(author_id=item.author_id, resolved_by=item.resolved_by)
    return result


def close_work(db, row, outcome, actor_id):
    db.execute(update(ContentReport).where(*matching(ContentReport, row), ContentReport.status == "OPEN").values(status="CLOSED"))
    appeal = open_appeal(db, row)
    if appeal:
        appeal.status, appeal.outcome = "CLOSED", outcome
        appeal.resolved_by, appeal.resolved_at = actor_id, int(time.time())
    claim = db.get(ReviewClaim, (kind_of(row), row.id))
    if claim:
        db.delete(claim)


def effective_review(db, row, now=None):
    if row.review_status != "UNDER_REVIEW":
        return row.review_status
    claim = db.get(ReviewClaim, (kind_of(row), row.id))
    now = int(time.time()) if now is None else now
    if claim and claim.content_revision == row.content_revision and claim.lease_until > now:
        return "UNDER_REVIEW"
    return "APPEALED" if open_appeal(db, row) else "QUEUED"


def check_claim(db, row, user):
    claim = db.get(ReviewClaim, (kind_of(row), row.id))
    if claim and claim.content_revision == row.content_revision and claim.lease_until > int(time.time()) and claim.reviewer_id != user.id:
        raise HTTPException(409, "Another reviewer holds the active lease")


def user_status(db, row, user):
    # Author response deliberately excludes reporter/reviewer identity and internal audit.
    result = {"entity_type": kind_of(row), "content": output(row, user)}
    result["content"]["review_status"] = effective_review(db, row)
    reason = db.scalar(select(ContentAudit.reason).where(*matching(ContentAudit, row),
        ContentAudit.event.in_(["MANUAL_HIDE", "ADMIN_HIDE", "MANUAL_APPROVE", "MANUAL_RESTORE", "APPEAL_RESOLVED"]))
        .order_by(ContentAudit.created_at.desc(), ContentAudit.decision_version.desc()).limit(1))
    result["decision_reason"] = reason
    appeals = db.scalars(select(Appeal).where(Appeal.entity_type == kind_of(row), Appeal.entity_id == row.id)
        .order_by(Appeal.created_at.desc(), Appeal.id.desc()).limit(20)).all()
    result["appeals"] = [appeal_output(item) for item in appeals]
    result["can_appeal"] = row.visibility_status in {"HIDDEN", "HELD_FOR_REVIEW"} and not open_appeal(db, row)
    return result


def staff_detail(db, row, user):
    result = {"entity_type":kind_of(row), "content":output(row, user), "policy_version":row.policy_version}
    result["content"]["review_status"] = effective_review(db, row)
    deleted = row.visibility_status == "DELETED_BY_AUTHOR"
    context = []
    if isinstance(row, Comment) and not deleted:
        post = db.get(Post, row.post_id)
        if post:
            context.append({"entity_type":"post", **output(post, user)})
        parent_id, seen = row.parent_id, set()
        parents = []
        while parent_id and parent_id not in seen and len(seen) < 32:
            seen.add(parent_id)
            parent = db.get(Comment, parent_id)
            if parent is None or parent.post_id != row.post_id:
                break
            parents.append({"entity_type":"comment", **output(parent, user)})
            parent_id = parent.parent_id
        context.extend(reversed(parents))
    result["parent_context"] = context
    ai = db.scalar(select(ModerationResult).join(ModerationJob, ModerationJob.id == ModerationResult.job_id)
        .where(*matching(ModerationJob, row)).order_by(ModerationResult.created_at.desc()).limit(1))
    result["ai"] = None if deleted or not ai else json.loads(ai.signals_json)
    job = db.scalar(select(ModerationJob).where(*matching(ModerationJob, row)))
    result["job"] = None if job is None else {key:getattr(job,key) for key in
        ("id", "status", "attempts", "total_attempts", "last_error", "next_retry_at", "outcome")}
    result["appeals"] = [appeal_output(item, True) for item in db.scalars(select(Appeal).where(
        Appeal.entity_type == kind_of(row), Appeal.entity_id == row.id).order_by(Appeal.created_at.desc(), Appeal.id.desc()).limit(50))]
    # Reporter identity never needed by the review UI, even with staff privileges.
    reports = db.scalars(select(ContentReport).where(*matching(ContentReport,row)).order_by(ContentReport.created_at).limit(50))
    result["reports"] = [{key:getattr(item,key) for key in ("id", "reason", "status", "created_at")} for item in reports]
    claim = db.get(ReviewClaim, (kind_of(row), row.id))
    result["claim"] = None if not claim or claim.lease_until <= int(time.time()) else {
        "reviewer_id":claim.reviewer_id, "lease_until":claim.lease_until}
    return result


def decision_audit(db, row, user, event, before, reason, **details):
    ai = db.scalar(select(ModerationResult).join(ModerationJob).where(*matching(ModerationJob,row)).limit(1))
    details.update(review_status=row.review_status, risk_tier=row.risk_tier,
        model_version=ai.model_version if ai else None, lexicon_version=ai.lexicon_version if ai else None,
        job_id=ai.job_id if ai else None, request_id=ai.request_id if ai else None)
    audit(db, row, user, event, before, reason, details)
