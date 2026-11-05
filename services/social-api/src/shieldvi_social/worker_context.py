from datetime import datetime, timezone

from sqlalchemy import select

from .models import Comment, Post
from .moderation_contract import ModerationRequest


def payload_for(db, job, row):
    context = {}
    parent_id = None
    post_id = row.id if isinstance(row, Post) else row.post_id

    def add_branch(item):
        branch, seen = [], set()
        while item and item.id not in context:
            if item.id == row.id or item.id in seen or item.post_id != post_id or item.visibility_status == "DELETED_BY_AUTHOR":
                return
            seen.add(item.id); branch.append(item)
            item = db.get(Comment, item.parent_id) if item.parent_id else None
        if len(context) + len(branch) > 50:
            return
        for entry in reversed(branch):
            context[entry.id] = {"comment_id":entry.id, "user_id":entry.author_id, "text":entry.body[:1000],
                "timestamp":datetime.fromtimestamp(entry.created_at, tz=timezone.utc),
                "parent_id":entry.parent_id, "mentioned_user_ids":[]}

    if isinstance(row, Comment):
        post = db.get(Post, post_id)
        if post is None or post.visibility_status == "DELETED_BY_AUTHOR":
            raise ValueError("ANCESTOR_DELETED")
        context["post:"+post.id] = {"comment_id":"post:"+post.id, "user_id":post.author_id,
            "text":post.body[:1000], "timestamp":datetime.fromtimestamp(post.created_at, tz=timezone.utc),
            "parent_id":None, "mentioned_user_ids":[]}
        parent_id = row.parent_id
        if parent_id:
            add_branch(db.get(Comment, parent_id))
            if parent_id not in context:
                raise ValueError("CONTEXT_UNAVAILABLE")
        recent = db.scalars(select(Comment).where(Comment.post_id == post_id, Comment.id != row.id,
            Comment.visibility_status != "DELETED_BY_AUTHOR", Comment.created_at <= row.created_at,
            Comment.updated_at <= row.created_at).order_by(Comment.created_at.desc(), Comment.id.desc()).limit(20)).all()
        for entry in recent:
            add_branch(entry)
    return ModerationRequest(schema_version="1.0", request_id=job.request_id, content_id=row.id,
        content_type="post" if isinstance(row, Post) else "comment", content_revision=row.content_revision,
        user_id=row.author_id, text=row.body, timestamp=datetime.fromtimestamp(row.created_at, tz=timezone.utc),
        parent_id=parent_id, mentioned_user_ids=[], language_hint="vi",
        context={"post_id":post_id, "source":"social-api", "complete":False, "recent_comments":list(context.values())})
