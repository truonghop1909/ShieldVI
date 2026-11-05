"""Reuse original worker transactions/CAS; add snapshot dependency guard."""
import uuid
from sqlalchemy.orm import object_session
from .worker import Worker
from .models import Post,Comment

class ConversationWorker(Worker):
    def owned(self,job,claim,now):
        if not super().owned(job,claim,now):return False
        # Worker.finish already holds the post/content lock in this SAME
        # transaction. Every canonical mutation takes that lock as well.
        db=object_session(job)
        for previous in claim.payload.context.recent_comments:
            is_post=previous.comment_id.startswith('post:')
            source=db.get(Post if is_post else Comment,previous.comment_id[5:] if is_post else previous.comment_id)
            same=source is not None and source.visibility_status!='DELETED_BY_AUTHOR' and source.body[:1000]==previous.text and source.author_id==previous.user_id
            if not same:
                # Drop stale analysis; a fresh request snapshot gets a new
                # correlation ID. Attempts remain bounded by original worker.
                job.status='RETRY_WAIT';job.last_error='CONTEXT_CHANGED';job.next_retry_at=now+1
                job.request_id=str(uuid.uuid4());job.request_hash=None;job.request_json=None
                job.claim_token=None;job.lease_until=None
                return False
        return True
