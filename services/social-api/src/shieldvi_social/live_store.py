"""Opt-in durable notifications, using the existing Social transaction/worker."""
import time
from datetime import datetime,timezone
from sqlalchemy import Integer,BigInteger,String,ForeignKey,Index,event,select
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,Session
from .models import Post,Comment,User,ModerationJob,ModerationResult,ContentAudit,Appeal
from .live_contract import LiveEventEnvelope,status_for
from .worker import require_schema

class LiveBase(DeclarativeBase):pass

class LiveMarker(LiveBase):
    __tablename__='live_schema_version'
    name:Mapped[str]=mapped_column(String(40),primary_key=True)

class LiveMember(LiveBase):
    __tablename__='live_thread_members'
    thread_id:Mapped[str]=mapped_column(ForeignKey(Post.id),primary_key=True)
    user_id:Mapped[str]=mapped_column(ForeignKey(User.id),primary_key=True)
    joined_ms:Mapped[int]=mapped_column(BigInteger,default=lambda:time.time_ns()//1_000_000)

class LiveEvent(LiveBase):
    __tablename__='live_events'
    __table_args__=(Index('ix_live_thread_cursor','thread_id','id'),{'sqlite_autoincrement':True})
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    thread_id:Mapped[str]=mapped_column(ForeignKey(Post.id),nullable=False)
    content_id:Mapped[str]=mapped_column(String(36),nullable=False)
    event_type:Mapped[str]=mapped_column(String(60),nullable=False)
    content_revision:Mapped[int]=mapped_column(Integer,nullable=False)
    decision_version:Mapped[int]=mapped_column(Integer,nullable=False)
    analysis_revision:Mapped[int|None]=mapped_column(Integer,nullable=True)
    analysis_status:Mapped[str]=mapped_column(String(20),nullable=False)
    correlation_id:Mapped[str|None]=mapped_column(String(36),nullable=True)
    created_ms:Mapped[int]=mapped_column(BigInteger,nullable=False,default=lambda:time.time_ns()//1_000_000)

def initialize(engine):
    require_schema(engine)
    LiveBase.metadata.create_all(engine)
    with engine.begin() as connection:
        values=connection.execute(select(LiveMarker.name)).scalars().all()
        if not values:connection.execute(LiveMarker.__table__.insert().values(name='live-1.0'))
        elif values!=['live-1.0']:raise RuntimeError('Unsupported live extension schema')

def require_live_schema(engine):
    require_schema(engine)
    with engine.connect() as connection:
        if connection.execute(select(LiveMarker.name)).scalars().all()!=['live-1.0']:
            raise RuntimeError('Initialize live schema explicitly before running the extension')

def envelope(row):
    return LiveEventEnvelope(event_id=row.id,event_type=row.event_type,thread_id=row.thread_id,content_id=row.content_id,
        content_revision=row.content_revision,decision_version=row.decision_version,analysis_revision=row.analysis_revision,
        analysis_status=row.analysis_status,correlation_id=row.correlation_id,created_at=datetime.fromtimestamp(row.created_ms/1000,tz=timezone.utc))

def _enabled(db):return bool(getattr(db.get_bind(),'shieldvi_live_events',False))

@event.listens_for(Session,'before_flush')
def _capture(db,flush_context,instances):
    if not _enabled(db):return
    captured=[]
    for obj in list(db.new)+list(db.dirty):
        if not isinstance(obj,(Post,Comment,ModerationJob,ModerationResult,ContentAudit,Appeal)):continue
        if obj not in db.new and not db.is_modified(obj,include_collections=False):continue
        if isinstance(obj,Comment) and obj in db.new and db.info.get('live_membership_required'):
            post_id,user_id=db.info['live_membership_required']
            if (obj.post_id,obj.author_id)!=(post_id,user_id) or db.get(LiveMember,(post_id,user_id)) is None:
                from fastapi import HTTPException
                raise HTTPException(403,'Thread membership required')
        captured.append((obj,obj in db.new))
    db.info['live_captured']=captured

@event.listens_for(Session,'after_flush_postexec')
def _append(db,flush_context):
    if not _enabled(db):return
    captured=db.info.pop('live_captured',[])
    for obj,is_new in captured:
        job=None
        if isinstance(obj,(Post,Comment)):
            row=obj;kind='conversation.message.created' if is_new else 'conversation.content.updated'
        elif isinstance(obj,ModerationJob):
            job=obj;row=db.get(Post if obj.entity_type=='post' else Comment,obj.entity_id)
            kind='moderation.analysis.failed' if obj.status=='FAILED_PERMANENTLY' else 'moderation.job.updated'
        elif isinstance(obj,ModerationResult):
            job=db.get(ModerationJob,obj.job_id);row=db.get(Post if job.entity_type=='post' else Comment,job.entity_id) if job else None
            kind='moderation.analysis.updated'
        else:
            if isinstance(obj,ContentAudit) and (obj.event in {'CREATE','EDIT'} or obj.event.startswith('AI_')):continue
            row=db.get(Post if obj.entity_type=='post' else Comment,obj.entity_id);kind='moderation.review.updated'
        if row is None:continue
        tid=row.id if isinstance(row,Post) else row.post_id
        db.add(LiveEvent(thread_id=tid,content_id=row.id,event_type=kind,content_revision=row.content_revision,
            decision_version=row.decision_version,analysis_revision=job.content_revision if job else None,
            analysis_status=status_for(job) if job else ('SUPERSEDED' if row.visibility_status=='DELETED_BY_AUTHOR' else 'QUEUED' if row.visibility_status=='PENDING_MODERATION' else 'NOT_ANALYZED'),
            correlation_id=job.request_id if job else None))
        if isinstance(obj,(Post,Comment)) and not is_new:
            # Existing edit/delete uses a bulk SQL invalidation, bypassing ORM
            # dirty tracking for jobs. Persist the terminal notice atomically
            # with the content change without altering that frozen behavior.
            stale=db.scalars(select(ModerationJob).where(ModerationJob.entity_id==row.id,
                ModerationJob.entity_type=='post' if isinstance(row,Post) else ModerationJob.entity_type=='comment',
                ModerationJob.outcome=='STALE_IGNORED').execution_options(populate_existing=True)).all()
            for previous in stale:
                exists=db.scalar(select(LiveEvent.id).where(LiveEvent.correlation_id==previous.request_id,LiveEvent.analysis_status=='SUPERSEDED').limit(1))
                if exists is None:db.add(LiveEvent(thread_id=tid,content_id=row.id,event_type='moderation.job.updated',
                    content_revision=row.content_revision,decision_version=row.decision_version,analysis_revision=previous.content_revision,
                    analysis_status='SUPERSEDED',correlation_id=previous.request_id))
    if any(isinstance(obj,Comment) for obj,_ in captured):db.info.pop('live_membership_required',None)

@event.listens_for(Session,'after_rollback')
def _rollback(db):
    db.info.pop('live_captured',None);db.info.pop('live_membership_required',None)
