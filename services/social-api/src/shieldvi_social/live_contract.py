"""Minimal durable notification envelope; text/evidence require authorized reads."""
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import AwareDatetime,BaseModel,ConfigDict,Field

LiveStatus=Literal['QUEUED','PROCESSING','COMPLETED','RETRYING','FAILED','SUPERSEDED','NOT_ANALYZED']
class LiveEventEnvelope(BaseModel):
    model_config=ConfigDict(extra='forbid')
    schema_version:Literal['live-1.0']='live-1.0'
    event_id:int=Field(ge=1)
    event_type:Literal['conversation.message.created','conversation.content.updated','moderation.job.updated',
        'moderation.analysis.updated','moderation.analysis.failed','moderation.review.updated']
    thread_id:UUID
    content_id:UUID
    content_revision:int=Field(ge=1)
    decision_version:int=Field(ge=0)
    analysis_revision:int|None=Field(default=None,ge=1)
    analysis_status:LiveStatus
    correlation_id:UUID|None=None
    created_at:AwareDatetime

def status_for(job):
    if job is None:return 'NOT_ANALYZED'
    if job.outcome=='STALE_IGNORED':return 'SUPERSEDED'
    return {'QUEUED':'QUEUED','PROCESSING':'PROCESSING','SUCCEEDED':'COMPLETED',
            'RETRY_WAIT':'RETRYING','FAILED_PERMANENTLY':'FAILED'}[job.status]

def accept_update(previous:LiveEventEnvelope|None,incoming:LiveEventEnvelope)->bool:
    if previous is None:return True
    if incoming.thread_id!=previous.thread_id or incoming.content_id!=previous.content_id:
        raise ValueError('Compare revisions only within the same content/thread')
    return incoming.event_id>previous.event_id and (incoming.content_revision,incoming.decision_version)>=(previous.content_revision,previous.decision_version)
