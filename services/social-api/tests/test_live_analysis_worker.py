"""Snapshot-safe original worker extension; deterministic AI fixture explicitly."""
import json,secrets,sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select
from shieldvi_social.db import make_engine
from shieldvi_social.live_store import initialize
from shieldvi_social.live_app import create_app
from shieldvi_social.live_analysis_worker import ConversationWorker
from shieldvi_social.live_ai_client import validate_live
from shieldvi_social.live_analysis_contract import LiveModerationResponse
from shieldvi_social.moderation_contract import ModerationResponse
from shieldvi_social.models import Post,Comment,ModerationJob,ModerationResult
from shieldvi_social.ai_client import WorkerSettings,AIError
from conftest import migrate
from test_content import actor,post,comment,versions,key_headers
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'services/moderation-ai'))
from app.live_analysis import IncrementalAnalyzer

class FakePredictor:
    threshold=.41;name='unit_fake_scores_not_real_inference'
    def predict_scores(self,texts):return [.02]*len(texts)

class FixtureAI:
    def __init__(self):self.analyzer=IncrementalAnalyzer(FakePredictor(),'a'*64)
    def moderate(self,payload):
        result=LiveModerationResponse.model_validate(self.analyzer.analyze(payload).model_dump(mode='json'))
        return validate_live(payload,result)

@pytest.fixture
def setup(settings):
    engine=make_engine(settings);migrate(engine);initialize(engine);engine.dispose()
    with TestClient(create_app(settings)) as client:
        headers=actor(client,'incremental_owner');thread=post(client,headers).json()
        worker=ConversationWorker(client.app.state.engine,WorkerSettings(service_token=SecretStr(secrets.token_urlsafe(32))),FixtureAI())
        assert worker.run_once()
        yield client,headers,thread,worker

def test_base_worker_validation_preserves_live_subclass_and_stores_signals(setup):
    client,headers,thread,worker=setup;row=comment(client,headers,thread['id']).json();assert worker.run_once()
    with client.app.state.sessions() as db:
        job=db.scalar(select(ModerationJob).where(ModerationJob.entity_id==row['id']))
        saved=db.get(ModerationResult,job.id);assert saved is not None
        assert json.loads(saved.signals_json)['conversation_signals']['processor']=='default-v5'

def test_parent_edit_during_inference_invalidates_snapshot_in_same_finish_transaction(setup):
    client,headers,thread,worker=setup;row=comment(client,headers,thread['id']).json();claim=worker.claim()
    current=client.get('/api/v1/posts/'+thread['id'],headers=headers).json()
    assert client.patch('/api/v1/posts/'+thread['id'],headers=headers,json={'body':'Changed parent context',**versions(current)}).status_code==200
    result=worker.ai.moderate(claim.payload);assert ModerationResponse.model_validate(result) is result
    assert not worker.finish(claim,response=result)
    with client.app.state.sessions() as db:
        job=db.get(ModerationJob,claim.job_id)
        assert job.status=='RETRY_WAIT' and job.last_error=='CONTEXT_CHANGED' and job.request_id!=claim.payload.request_id
        assert db.get(ModerationResult,claim.job_id) is None

def test_research_processor_is_rejected_by_live_worker_client(setup):
    client,headers,thread,worker=setup;comment(client,headers,thread['id']);claim=worker.claim();result=worker.ai.moderate(claim.payload)
    result.conversation_signals.processor='experimental-v6.2'
    with pytest.raises(AIError,match='UNAPPROVED_PROCESSOR'):validate_live(claim.payload,result)

def test_new_reply_payload_contains_original_post_and_parent_without_account_pii(setup):
    client,headers,thread,worker=setup
    parent=comment(client,headers,thread['id'],body='Synthetic parent context').json();assert worker.run_once()
    child=comment(client,headers,thread['id'],parent_id=parent['id'],body='Synthetic reply').json()
    claim=worker.claim();rows={row.comment_id:row for row in claim.payload.context.recent_comments}
    assert claim.payload.content_id==child['id']
    assert rows['post:'+thread['id']].text==thread['body']
    assert rows[parent['id']].text==parent['body']
    assert claim.payload.parent_id==parent['id']
    wire=claim.payload.model_dump_json()
    assert 'incremental_owner' not in wire and '@' not in wire

def test_forged_instance_with_unknown_user_is_rejected(setup):
    client,headers,thread,worker=setup;comment(client,headers,thread['id']);claim=worker.claim();result=worker.ai.moderate(claim.payload)
    from shieldvi_social.live_analysis_contract import GroundedInstance
    result.conversation_signals.attack_instances=[GroundedInstance(comment_id=claim.payload.content_id,actor_user_id=claim.payload.user_id,
        target_user_id='unknown',timestamp=claim.payload.timestamp,context_confidence='medium',target_confidence='medium',
        target_method='addressed_reply',target_evidence_ids=[claim.payload.content_id])]
    with pytest.raises(AIError,match='INVALID_INSTANCE'):validate_live(claim.payload,result)

@pytest.mark.parametrize('text,is_attack',[('Mình đồng ý, cảm ơn bạn đã giải thích.',False),('Mày là đồ ngu, im đi.',True)])
def test_reply_recipient_is_separate_from_attack_target_without_sending_usernames_to_ai(setup,text,is_attack):
    client,owner,thread,worker=setup;parent=comment(client,owner,thread['id'],body='Mình chia sẻ lịch thảo luận.').json();assert worker.run_once()
    sender=actor(client,'reply_sender')
    assert client.post(f"/api/live/threads/{thread['id']}/join",headers=sender).status_code==200
    response=client.post(f"/api/live/threads/{thread['id']}/messages",headers=key_headers(sender),json={'body':text,'parent_id':parent['id']})
    assert response.status_code==201;row=response.json();assert row['author_username']=='reply_sender' and row['reply_to_username']=='incremental_owner'
    claim=worker.claim();assert claim.payload.parent_id==parent['id'] and claim.payload.text==text
    assert 'reply_sender' not in claim.payload.model_dump_json() and 'incremental_owner' not in claim.payload.model_dump_json()
    result=worker.ai.moderate(claim.payload);current=result.conversation_signals.current
    assert current.reply_to_user_id==parent['author_id']
    assert current.attack_instance_candidate is is_attack
    assert current.directed_at_user_id==(parent['author_id'] if is_attack else None)
    assert current.policy_executed is False
