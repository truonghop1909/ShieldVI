"""Staff queue, author appeals and privacy-preserving reports."""
import json
import time
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, case, func, literal, or_, select, union_all, update
from sqlalchemy.orm import Session

from .content_store import audit, invalidate_jobs, output, rate_limit, require_versions, visible_comment
from .dependencies import Principal, content_writer, current_principal, get_content_write_db, get_db, require_roles
from .models import Appeal, Comment, ContentAudit, ContentReport, ModerationJob, ModerationResult, Post, PUBLIC_VISIBILITY, ReviewClaim
from .moderation_routes import ReviewInput, staff_writer
from .review_store import appeal_output, check_claim, close_work, decision_audit, effective_review, kind_of, matching, open_appeal, staff_detail, user_status
from .worker import locked_content

router = APIRouter(prefix="/api/v1", tags=["moderation-review"])
Entity = Literal["post", "comment"]
staff_reader = require_roles("moderator", "admin")


def find(db, kind, entity_id, lock=False):
    row = locked_content(db, kind, str(entity_id)) if lock else db.get(Post if kind == "post" else Comment, str(entity_id))
    if row is None:
        raise HTTPException(404, "Content not found")
    return row


def page_result(db, query, page, size, transform):
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    rows = db.execute(query.offset((page-1)*size).limit(size)).all()
    return {"items":[transform(item) for item in rows], "total":total, "page":page, "page_size":size}


@router.get("/moderation/queue")
def queue(tab: Literal["review","reports","appeals","failed","all"] = "review",
          entity_type: Literal["all","post","comment"] = "all",
          page: int = Query(1, ge=1, le=10000), page_size: int = Query(20, ge=1, le=50),
          principal: Principal = Depends(staff_reader), db: Session = Depends(get_db)):
    queries = []
    for kind, model in (("post",Post),("comment",Comment)):
        if entity_type not in {"all",kind}:
            continue
        reports = select(func.count()).select_from(ContentReport).where(ContentReport.entity_type == kind,
            ContentReport.entity_id == model.id, ContentReport.content_revision == model.content_revision,
            ContentReport.status == "OPEN").correlate(model).scalar_subquery()
        appeals = select(Appeal.id).where(Appeal.entity_type == kind, Appeal.entity_id == model.id,
            Appeal.content_revision == model.content_revision, Appeal.status == "OPEN").correlate(model).exists()
        job_match = and_(ModerationJob.entity_type == kind, ModerationJob.entity_id == model.id,
            ModerationJob.content_revision == model.content_revision)
        failed = and_(ModerationJob.status == "FAILED_PERMANENTLY", model.visibility_status == "PENDING_MODERATION",
            ModerationJob.expected_decision_version == model.decision_version)
        repeated = ModerationResult.signals_json.contains('"suspected_repeated_harassment": true')
        priority = case((model.visibility_status == "HELD_FOR_REVIEW",0),(failed,1),
            (model.visibility_status == "PENDING_MODERATION",2),(appeals,3),(repeated,4),else_=5)
        conditions = {"review":model.review_status.in_(["QUEUED","UNDER_REVIEW","APPEALED"]),
            "reports":reports > 0, "appeals":appeals, "failed":failed, "all":literal(True)}
        queries.append(select(literal(kind).label("entity_type"), model.id.label("id"), priority.label("priority"),
            reports.label("report_count"), model.created_at.label("created_at"))
            .outerjoin(ModerationJob, job_match).outerjoin(ModerationResult, ModerationResult.job_id == ModerationJob.id)
            .where(model.visibility_status != "DELETED_BY_AUTHOR", conditions[tab]))
    combined = union_all(*queries).subquery()
    query = select(combined).order_by(combined.c.priority, combined.c.created_at,
        combined.c.report_count.desc(), combined.c.entity_type, combined.c.id)
    def item(record):
        row = find(db, record.entity_type, record.id)
        content = output(row, principal.user)
        content["review_status"] = effective_review(db,row)
        return {"entity_type":record.entity_type, "content":content,
            "priority":record.priority, "report_count":record.report_count}
    return page_result(db, query, page, page_size, item)


@router.get("/moderation/content/{kind}/{entity_id}")
def detail(kind: Entity, entity_id: UUID, principal: Principal = Depends(staff_reader), db: Session = Depends(get_db)):
    return staff_detail(db, find(db,kind,entity_id), principal.user)


@router.get("/moderation/content/{kind}/{entity_id}/audit")
def history(kind: Entity, entity_id: UUID, page: int = Query(1,ge=1,le=10000),
            page_size: int = Query(20,ge=1,le=50), principal: Principal = Depends(staff_reader), db: Session = Depends(get_db)):
    find(db,kind,entity_id)
    query = select(ContentAudit).where(ContentAudit.entity_type == kind, ContentAudit.entity_id == str(entity_id))
    query = query.order_by(ContentAudit.created_at.desc(),ContentAudit.decision_version.desc(),ContentAudit.id.desc())
    def item(record):
        row = record[0]
        data = {key:getattr(row,key) for key in ("id","actor_id","actor_type","actor_role","actor_identifier",
            "event","reason","content_revision","decision_version","before_visibility","after_visibility","policy_version","created_at")}
        data["details"] = json.loads(row.details_json) if row.details_json else None
        return data
    return page_result(db, query, page, page_size, item)


@router.post("/moderation/content/{kind}/{entity_id}/claim")
def claim(kind: Entity, entity_id: UUID, payload: ReviewInput, request: Request,
          principal: Principal = Depends(staff_writer), db: Session = Depends(get_content_write_db)):
    rate_limit(db,request.app.state.settings,principal.user)
    row = find(db,kind,entity_id,True)
    require_versions(row,payload)
    if row.visibility_status == "DELETED_BY_AUTHOR" or effective_review(db,row) not in {"QUEUED","APPEALED","UNDER_REVIEW"}:
        raise HTTPException(409,"Content is not awaiting review")
    check_claim(db,row,principal.user)
    old = db.get(ReviewClaim,(kind,row.id))
    previous = "APPEALED" if open_appeal(db,row) else "QUEUED"
    if old:
        old.reviewer_id, old.content_revision, old.previous_review = principal.user.id,row.content_revision,previous
        old.lease_until = int(time.time())+300
    else:
        db.add(ReviewClaim(entity_type=kind,entity_id=row.id,content_revision=row.content_revision,
            reviewer_id=principal.user.id,previous_review=previous,lease_until=int(time.time())+300))
    invalidate_jobs(db,row)
    row.review_status, row.decision_version, row.updated_at = "UNDER_REVIEW",row.decision_version+1,int(time.time())
    decision_audit(db,row,principal.user,"REVIEW_CLAIM",row.visibility_status,payload.reason)
    db.commit()
    return staff_detail(db,row,principal.user)


@router.get("/me/moderation")
def mine(page: int = Query(1,ge=1,le=10000),page_size: int = Query(20,ge=1,le=50),
         principal: Principal = Depends(current_principal),db: Session = Depends(get_db)):
    queries = [select(literal(kind).label("kind"),model.id.label("id"),model.updated_at.label("updated_at"))
        .where(model.author_id == principal.user.id,model.visibility_status != "DELETED_BY_AUTHOR")
        for kind,model in (("post",Post),("comment",Comment))]
    combined = union_all(*queries).subquery()
    return page_result(db,select(combined).order_by(combined.c.updated_at.desc(),combined.c.id),page,page_size,
        lambda item:user_status(db,find(db,item.kind,item.id),principal.user))


@router.get("/content/{kind}/{entity_id}/moderation")
def status(kind: Entity,entity_id: UUID,principal: Principal = Depends(current_principal),db: Session = Depends(get_db)):
    row = find(db,kind,entity_id)
    if row.author_id != principal.user.id:
        raise HTTPException(404,"Content not found")
    return user_status(db,row,principal.user)


@router.post("/content/{kind}/{entity_id}/reports")
def report(kind: Entity,entity_id: UUID,payload: ReviewInput,request: Request,
           principal: Principal = Depends(content_writer),db: Session = Depends(get_content_write_db)):
    rate_limit(db,request.app.state.settings,principal.user)
    row = find(db,kind,entity_id,True)
    # Reports require effective PUBLIC visibility, including all ancestors, for any role.
    public = row.visibility_status in PUBLIC_VISIBILITY
    if isinstance(row,Comment):
        from types import SimpleNamespace
        public = public and visible_comment(db,row,SimpleNamespace(id="",role="user"))
    if not public:
        raise HTTPException(404,"Content not found")
    require_versions(row,payload)
    if row.author_id == principal.user.id:
        raise HTTPException(403,"Authors cannot report their own content")
    prior = db.scalar(select(ContentReport).where(*matching(ContentReport,row),ContentReport.reporter_id == principal.user.id))
    if prior:
        return {"status":"RECEIVED"}
    db.add(ContentReport(entity_type=kind,entity_id=row.id,content_revision=row.content_revision,
        reporter_id=principal.user.id,reason=payload.reason))
    if row.review_status != "UNDER_REVIEW":
        row.review_status = "QUEUED"
    # Reporting does not override decisions or change visibility/risk/decision_version.
    audit(db,row,principal.user,"REPORT",row.visibility_status,payload.reason)
    db.commit()
    return {"status":"RECEIVED"}


@router.post("/content/{kind}/{entity_id}/appeals",status_code=201)
def appeal(kind: Entity,entity_id: UUID,payload: ReviewInput,request: Request,
           principal: Principal = Depends(content_writer),db: Session = Depends(get_content_write_db)):
    rate_limit(db,request.app.state.settings,principal.user)
    row = find(db,kind,entity_id,True)
    if row.author_id != principal.user.id:
        raise HTTPException(404,"Content not found")
    require_versions(row,payload)
    if row.visibility_status not in {"HIDDEN","HELD_FOR_REVIEW"} or open_appeal(db,row):
        raise HTTPException(409,"Content is not eligible for appeal")
    item = Appeal(entity_type=kind,entity_id=row.id,content_revision=row.content_revision,
        appealed_decision_version=row.decision_version,author_id=principal.user.id,reason=payload.reason)
    db.add(item)
    invalidate_jobs(db,row)
    claim = db.get(ReviewClaim,(kind,row.id))
    if claim:
        db.delete(claim)
    row.review_status,row.decision_version,row.updated_at = "APPEALED",row.decision_version+1,int(time.time())
    db.flush()
    decision_audit(db,row,principal.user,"APPEAL_OPENED",row.visibility_status,payload.reason,appeal_id=item.id)
    db.commit()
    return appeal_output(item)


class ResolveInput(ReviewInput):
    outcome: Literal["RESTORED","UPHELD"]


@router.post("/moderation/appeals/{appeal_id}/resolve")
def resolve(appeal_id: UUID,payload: ResolveInput,request: Request,
            principal: Principal = Depends(staff_writer),db: Session = Depends(get_content_write_db)):
    rate_limit(db,request.app.state.settings,principal.user)
    item = db.get(Appeal,str(appeal_id))
    if item is None:
        raise HTTPException(404,"Appeal not found")
    row = find(db,item.entity_type,item.entity_id,True)
    item = db.scalar(select(Appeal).where(Appeal.id == item.id).with_for_update().execution_options(populate_existing=True))
    require_versions(row,payload)
    check_claim(db,row,principal.user)
    if item.status != "OPEN" or item.content_revision != row.content_revision or row.visibility_status not in {"HIDDEN","HELD_FOR_REVIEW"}:
        raise HTTPException(409,"Appeal is no longer actionable")
    before = row.visibility_status
    close_work(db,row,"RESOLVED",principal.user.id)
    item.status,item.outcome,item.resolution_reason = "RESOLVED",payload.outcome,payload.reason
    item.resolved_by,item.resolved_at = principal.user.id,int(time.time())
    invalidate_jobs(db,row)
    row.visibility_status = "PUBLISHED" if payload.outcome == "RESTORED" else "HIDDEN"
    row.review_status,row.policy_version = "RESOLVED","manual-review-v1"
    row.decision_version,row.updated_at = row.decision_version+1,int(time.time())
    decision_audit(db,row,principal.user,"APPEAL_RESOLVED",before,payload.reason,appeal_id=item.id,outcome=payload.outcome)
    db.commit()
    return staff_detail(db,row,principal.user)
