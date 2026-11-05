"""Durable, single-job-at-a-time worker. Run separately from the web server."""
import argparse
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
import hashlib
import json
import random
import time
import uuid

from sqlalchemy import func, or_, select, text
from pydantic import ValidationError

from .ai_client import AIClient, AIError, WorkerSettings
from .config import Settings
from .db import make_engine, session_factory
from .models import Comment, ContentAudit, ModerationJob, ModerationResult, Post
from .moderation_contract import ModerationRequest, ModerationResponse
from .worker_context import payload_for
from .policy import policy_outcome

POLICY_VERSION = "social-policy-shadow-0.2"


def require_schema(engine):
    with engine.connect() as connection:
        if connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all() != ["0004_review"]:
            raise RuntimeError("Run alembic upgrade head before starting the worker")


def locked_content(db, kind, entity_id):
    model = Post if kind == "post" else Comment
    if model is Comment:
        initial = db.get(Comment, entity_id)
        if initial:
            db.execute(select(Post).where(Post.id == initial.post_id).with_for_update()).first()
    return db.scalar(select(model).where(model.id == entity_id).with_for_update().execution_options(populate_existing=True))


def current_content(row, job):
    return row is not None and row.content_revision == job.content_revision and row.decision_version == job.expected_decision_version and row.visibility_status == "PENDING_MODERATION"


def terminal(job, outcome):
    job.status, job.outcome = "SUCCEEDED", outcome
    job.claim_token, job.lease_until, job.request_json = None, None, None


def worker_audit(db, row, job, event, now, before=None):
    db.add(ContentAudit(entity_type=job.entity_type, entity_id=job.entity_id,
        content_revision=row.content_revision, decision_version=row.decision_version,
        actor_id=None, actor_type="system", actor_identifier="moderation-worker", actor_role="worker",
        event=event, reason=f"{event};job={job.id};request={job.request_id}",
        before_visibility=before or row.visibility_status, after_visibility=row.visibility_status,
        policy_version=job.policy_version, created_at=now))


@dataclass(frozen=True)
class Claim:
    job_id: str
    claim_token: str
    entity_type: str
    entity_id: str
    payload: ModerationRequest


class Worker:
    def __init__(self, engine, settings, ai, clock=time.time, jitter=random.random):
        self.engine, self.sessions, self.settings = engine, session_factory(engine), settings
        self.ai, self.clock, self.jitter = ai, clock, jitter
        require_schema(engine)

    @contextmanager
    def write(self):
        with self.sessions() as db:
            if self.engine.dialect.name == "sqlite":
                db.connection(execution_options={"sqlite_immediate": True})
            yield db
            db.commit()

    def claim(self):
        now = int(self.clock())
        with self.write() as db:
            ready = or_(
                (ModerationJob.status.in_(["QUEUED", "RETRY_WAIT"])) & (ModerationJob.next_retry_at <= now),
                (ModerationJob.status == "PROCESSING") & or_(ModerationJob.lease_until.is_(None), ModerationJob.lease_until <= now),
            )
            job = db.scalar(select(ModerationJob).where(ready).order_by(ModerationJob.created_at, ModerationJob.id)
                .with_for_update(skip_locked=True).limit(1))
            if job is None:
                return None
            row = db.get(Post if job.entity_type == "post" else Comment, job.entity_id)
            if not current_content(row, job):
                terminal(job, "STALE_IGNORED")
                return None
            if job.attempts >= self.settings.max_attempts:
                job.status, job.last_error = "FAILED_PERMANENTLY", "ATTEMPTS_EXHAUSTED"
                job.claim_token, job.lease_until, job.request_json = None, None, None
                worker_audit(db, row, job, "AI_FAILED", now)
                return None
            if job.policy_version not in {None, POLICY_VERSION}:
                job.status, job.last_error = "FAILED_PERMANENTLY", "POLICY_STALE"
                job.claim_token, job.lease_until, job.request_json = None, None, None
                worker_audit(db, row, job, "AI_FAILED", now)
                return None
            job.policy_version = POLICY_VERSION
            try:
                payload = ModerationRequest.model_validate_json(job.request_json) if job.request_json else payload_for(db, job, row)
            except (ValueError, ValidationError):
                job.status, job.last_error, job.request_json = "FAILED_PERMANENTLY", "CONTEXT_INVALID", None
                job.claim_token, job.lease_until = None, None
                worker_audit(db, row, job, "AI_FAILED", now)
                return None
            snapshot = payload.model_dump_json()
            digest = hashlib.sha256(snapshot.encode()).hexdigest()
            if job.request_hash and job.request_hash != digest:
                job.status, job.last_error = "FAILED_PERMANENTLY", "REQUEST_HASH_MISMATCH"
                job.request_json, job.claim_token, job.lease_until = None, None, None
                return None
            job.request_json, job.request_hash = snapshot, digest
            job.attempts += 1
            job.total_attempts += 1
            job.status, job.claim_token, job.lease_until = "PROCESSING", str(uuid.uuid4()), now + self.settings.lease_seconds
            return Claim(job.id, job.claim_token, job.entity_type, job.entity_id, payload)

    def owned(self, job, claim, now):
        return job is not None and job.status == "PROCESSING" and job.claim_token == claim.claim_token and job.lease_until > now

    def finish(self, claim, response=None, error=None):
        now = int(self.clock())
        with self.write() as db:
            row = locked_content(db, claim.entity_type, claim.entity_id)
            job = db.scalar(select(ModerationJob).where(ModerationJob.id == claim.job_id).with_for_update().execution_options(populate_existing=True))
            if not self.owned(job, claim, now):
                return False
            if (job.request_id, job.entity_id, job.content_revision) != (claim.payload.request_id, claim.payload.content_id, claim.payload.content_revision):
                job.status, job.last_error = "FAILED_PERMANENTLY", "STALE_REQUEST_METADATA"
                job.claim_token, job.lease_until, job.request_json = None, None, None
                if row:
                    worker_audit(db, row, job, "AI_FAILED", now)
                return False
            if not current_content(row, job):
                terminal(job, "STALE_IGNORED")
                return False
            if job.policy_version != POLICY_VERSION:
                job.status, job.last_error = "FAILED_PERMANENTLY", "POLICY_STALE"
                job.claim_token, job.lease_until, job.request_json = None, None, None
                worker_audit(db, row, job, "AI_FAILED", now)
                return False
            job.last_ai_check_at = now
            if error:
                job.last_error = error.code
                job.claim_token, job.lease_until = None, None
                row.risk_tier, row.review_status = "UNKNOWN", "QUEUED"
                if error.retryable and job.attempts < self.settings.max_attempts:
                    delay = 5 if job.attempts == 1 else 30
                    delay = max(delay + int(delay*.2*self.jitter()), error.retry_after)
                    job.status, job.next_retry_at = "RETRY_WAIT", now + delay
                    worker_audit(db, row, job, "AI_RETRY", now)
                else:
                    job.status, job.request_json = "FAILED_PERMANENTLY", None
                    worker_audit(db, row, job, "AI_FAILED", now)
                return True
            if db.get(ModerationResult, job.id):
                terminal(job, "DUPLICATE_IGNORED")
                return False
            before = row.visibility_status
            row.risk_tier, row.visibility_status, row.review_status = policy_outcome(response)
            row.policy_version, row.updated_at = POLICY_VERSION, now
            row.decision_version += 1
            signals = response.model_dump(mode="json")
            db.add(ModerationResult(job_id=job.id, request_id=job.request_id,
                content_revision=job.content_revision, model_version=response.model_version,
                lexicon_version=response.lexicon_version, threshold=response.model_threshold,
                ai_label=response.ai_label, score=response.toxicity_score, policy_version=POLICY_VERSION,
                risk_tier=row.risk_tier, signals_json=json.dumps(signals, ensure_ascii=False),
                analyzed_at=response.analyzed_at.isoformat(), created_at=now))
            job.last_error = None
            terminal(job, "APPLIED")
            worker_audit(db, row, job, "AI_APPLIED", now, before)
            return True

    def run_once(self):
        claim = self.claim()
        if claim is None:
            return False
        try:
            response = ModerationResponse.model_validate(self.ai.moderate(claim.payload))
            if (response.request_id, response.content_id, response.content_revision) != (claim.payload.request_id, claim.payload.content_id, claim.payload.content_revision):
                raise AIError("AI_CORRELATION_MISMATCH", True)
        except AIError as error:
            self.finish(claim, error=error)
        except (ValueError, ValidationError):
            self.finish(claim, error=AIError("AI_INVALID_SCHEMA", True))
        else:
            self.finish(claim, response=response)
        return True


def queue_stats(engine, now=None, db=None):
    if db is None:
        require_schema(engine)
    now = int(time.time() if now is None else now)
    # Authenticated HTTP readers must reuse their existing read transaction.
    # A second connection can block behind a pending writer whose commit is
    # waiting for that first reader, creating a SQLite lock cycle.
    with (nullcontext(db) if db is not None else session_factory(engine)()) as db:
        counts = dict(db.execute(select(ModerationJob.status, func.count()).group_by(ModerationJob.status)).all())
        oldest = db.scalar(select(func.min(ModerationJob.created_at)).where(ModerationJob.status.in_(["QUEUED", "RETRY_WAIT", "PROCESSING", "FAILED_PERMANENTLY"])))
        success = db.scalar(select(func.count()).select_from(ModerationJob).where(ModerationJob.last_ai_check_at >= now-300, ModerationJob.last_error.is_(None)))
        failures = db.scalar(select(func.count()).select_from(ModerationJob).where(ModerationJob.last_ai_check_at >= now-300, ModerationJob.last_error.is_not(None)))
        failed = db.scalars(select(ModerationJob).where(ModerationJob.status == "FAILED_PERMANENTLY").order_by(ModerationJob.created_at).limit(50)).all()
        attempted = db.scalar(select(func.count()).select_from(ModerationJob).where(ModerationJob.total_attempts > 0))
        total_attempts = db.scalar(select(func.sum(ModerationJob.total_attempts))) or 0
        expired = db.scalar(select(func.count()).select_from(ModerationJob).where(ModerationJob.status == "PROCESSING",
            or_(ModerationJob.lease_until.is_(None), ModerationJob.lease_until <= now)))
        return {"counts": counts, "queue_size":sum(counts.get(status,0) for status in ("QUEUED","PROCESSING","RETRY_WAIT")),
            "retry_attempts":total_attempts-attempted, "expired_leases":expired,
            "oldest_wait_seconds": max(0, now-oldest) if oldest is not None else 0,
            "model_availability": "degraded" if success and failures else "up" if success else "down" if failures else "unknown",
            "failed_jobs": [{"job_id":row.id, "entity_type":row.entity_type, "entity_id":row.entity_id,
                "attempts":row.attempts, "total_attempts":row.total_attempts, "error_code":row.last_error} for row in failed]}


def main():
    parser = argparse.ArgumentParser(description="ShieldVI durable moderation worker (shadow only)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--once", action="store_true")
    group.add_argument("--stats", action="store_true")
    args = parser.parse_args()
    engine = make_engine(Settings.from_env())
    ai = None
    try:
        if args.stats:
            print(json.dumps(queue_stats(engine), ensure_ascii=False))
            return
        settings = WorkerSettings.from_env()
        ai = AIClient(settings)
        worker = Worker(engine, settings, ai)
        if args.once:
            print(json.dumps({"processed":worker.run_once()}))
        else:
            while True:
                if not worker.run_once():
                    time.sleep(settings.poll_seconds)
    except KeyboardInterrupt:
        pass
    finally:
        if ai:
            ai.close()
        engine.dispose()


if __name__ == "__main__":
    main()
