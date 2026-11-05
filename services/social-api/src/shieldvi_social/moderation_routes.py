import time
import uuid
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from .content_store import audit, invalidate_jobs, output, rate_limit, require_versions
from .dependencies import Principal, content_writer, get_content_write_db, get_db, require_roles
from .models import ModerationJob
from .schemas import StrictInput
from .worker import current_content, locked_content, queue_stats

router = APIRouter(prefix="/api/v1/moderation", tags=["moderation-operations"])


class ReviewInput(StrictInput):
    expected_revision: int = Field(ge=1)
    expected_decision_version: int = Field(ge=0)
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def reason_required(cls, value):
        if not value.strip() or "\x00" in value or any(0xD800 <= ord(char) <= 0xDFFF for char in value):
            raise ValueError("Reason is required")
        return value


class DecisionInput(ReviewInput):
    entity_type: Literal["post", "comment"]
    entity_id: UUID
    action: Literal["approve", "hide", "restore"]
    false_positive: bool = Field(default=False, strict=True)


def staff_writer(principal: Principal = Depends(content_writer)):
    if principal.user.role not in {"moderator", "admin"}:
        raise HTTPException(403, "Insufficient permissions")
    return principal


@router.get("/jobs")
def jobs(request: Request, principal: Principal = Depends(require_roles("moderator", "admin")), db: Session = Depends(get_db)):
    return queue_stats(request.app.state.engine, db=db)


@router.post("/decisions")
def decide(payload: DecisionInput, request: Request, principal: Principal = Depends(staff_writer),
           db: Session = Depends(get_content_write_db)):
    rate_limit(db, request.app.state.settings, principal.user)
    row = locked_content(db, payload.entity_type, str(payload.entity_id))
    if row is None:
        raise HTTPException(404, "Content not found")
    require_versions(row, payload)
    if row.visibility_status == "DELETED_BY_AUTHOR":
        raise HTTPException(409, "Deleted content cannot be restored")
    from .review_store import check_claim, close_work, decision_audit, open_appeal
    check_claim(db, row, principal.user)
    if open_appeal(db, row):
        raise HTTPException(409, "Resolve the open appeal explicitly")
    if payload.action == "restore" and row.visibility_status not in {"HIDDEN", "HELD_FOR_REVIEW"}:
        raise HTTPException(409, "Only hidden or held content can be restored")
    if payload.action == "approve" and row.visibility_status in {"HIDDEN", "HELD_FOR_REVIEW"}:
        raise HTTPException(409, "Use restore for hidden or held content")
    if payload.false_positive and payload.action == "hide":
        raise HTTPException(422, "False-positive feedback requires approve or restore")
    before = row.visibility_status
    invalidate_jobs(db, row)
    close_work(db, row, "MANUAL_DECISION", principal.user.id)
    row.visibility_status = "HIDDEN" if payload.action == "hide" else "PUBLISHED"
    row.review_status = "REJECTED" if payload.action == "hide" else "APPROVED"
    row.decision_version += 1
    row.policy_version, row.updated_at = "manual-review-v1", int(time.time())
    decision_audit(db, row, principal.user, "MANUAL_" + payload.action.upper(), before, payload.reason,
        false_positive=payload.false_positive)
    db.commit()
    return output(row, principal.user)


@router.post("/jobs/{job_id}/retry")
def retry(job_id: UUID, payload: ReviewInput, request: Request,
          principal: Principal = Depends(staff_writer), db: Session = Depends(get_content_write_db)):
    rate_limit(db, request.app.state.settings, principal.user)
    initial = db.get(ModerationJob, str(job_id))
    if initial is None:
        raise HTTPException(404, "Job not found")
    row = locked_content(db, initial.entity_type, initial.entity_id)
    job = db.scalar(select(ModerationJob).where(ModerationJob.id == str(job_id)).with_for_update().execution_options(populate_existing=True))
    if job.status != "FAILED_PERMANENTLY" or not current_content(row, job):
        raise HTTPException(409, "Job is not eligible for manual retry")
    require_versions(row, payload)
    job.request_id, job.request_hash, job.request_json = str(uuid.uuid4()), None, None
    job.claim_token, job.lease_until, job.policy_version = None, None, None
    job.status, job.attempts, job.next_retry_at = "QUEUED", 0, int(time.time())
    job.retry_count += 1
    job.outcome, job.last_error, job.last_ai_check_at = None, None, None
    audit(db, row, principal.user, "JOB_RETRY", row.visibility_status, payload.reason)
    db.commit()
    return {"job_id":job.id, "status":job.status, "retry_count":job.retry_count}
