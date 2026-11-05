from datetime import datetime,timezone
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from shieldvi_social.live_contract import LiveEventEnvelope,status_for

def event():
    return {'event_id':1,'event_type':'conversation.message.created','thread_id':'00000000-0000-0000-0000-000000000001',
        'content_id':'00000000-0000-0000-0000-000000000002','content_revision':1,'decision_version':0,
        'analysis_status':'QUEUED','created_at':datetime.now(timezone.utc)}

def test_minimal_envelope_roundtrip_and_schema_matches_generated_file():
    data=event();wire=LiveEventEnvelope.model_validate(data).model_dump_json()
    assert LiveEventEnvelope.model_validate_json(wire).event_id==1
    schema=Path(__file__).resolve().parents[3]/'contracts/realtime_event.schema.json'
    assert json.loads(schema.read_text())==LiveEventEnvelope.model_json_schema()
    assert not {'body','text','token','score','evidence'}&set(json.loads(wire))

@pytest.mark.parametrize('key,value',[('event_id',0),('content_revision',0),('decision_version',-1),('analysis_status','TOXIC'),('created_at','2026-11-04T10:00:00'),('thread_id','../../private')])
def test_rejects_bad_identity_revision_status_or_naive_time(key,value):
    data=event();data[key]=value
    with pytest.raises(ValidationError):LiveEventEnvelope.model_validate(data)

def test_payload_cannot_leak_text_token_or_evidence():
    for key in ('body','text','token','evidence'):
        with pytest.raises(ValidationError):LiveEventEnvelope.model_validate({**event(),key:'private'})

def test_stale_status_is_not_completed():
    class Job:status='SUCCEEDED';outcome='STALE_IGNORED'
    assert status_for(Job())=='SUPERSEDED' and status_for(None)=='NOT_ANALYZED'

@pytest.mark.parametrize('changes,expected',[({'event_id':2},True),({'event_id':1},False),({'event_id':2,'content_revision':1},False),({'event_id':2,'decision_version':1},False)])
def test_ordering_and_stale_revisions(changes,expected):
    from shieldvi_social.live_contract import accept_update
    previous=LiveEventEnvelope.model_validate({**event(),'content_revision':2,'decision_version':2})
    incoming=previous.model_copy(update=changes)
    assert accept_update(previous,incoming)==expected
