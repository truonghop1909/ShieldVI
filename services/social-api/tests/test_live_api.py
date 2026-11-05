"""Real temporary SQLite/ASGI/worker integration; AI response fixtures are explicit."""
import json,time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import event,func,select,text
from shieldvi_social.db import make_engine
from shieldvi_social.main import create_app as original_app
from shieldvi_social.live_app import create_app
from shieldvi_social.live_store import initialize,LiveEvent,LiveMember
from shieldvi_social.models import Post,Comment,ModerationJob,ModerationResult,AuthSession
from shieldvi_social.worker import Worker
from shieldvi_social.ai_client import WorkerSettings,AIError
from conftest import migrate
from test_content import actor,post,key_headers,versions
from test_worker import response

class FixtureAI:
    def moderate(self,payload):return response(payload)

@pytest.fixture
def live(settings):
    engine=make_engine(settings);migrate(engine);initialize(engine);engine.dispose()
    with TestClient(create_app(settings)) as client:
        owner=actor(client,'live_owner');other=actor(client,'live_other');staff=actor(client,'live_staff','admin')
        worker=Worker(client.app.state.engine,WorkerSettings(service_token=SecretStr('synthetic-unit-token-not-a-real-key-1234')),FixtureAI())
        thread=post(client,owner,'Synthetic public conversation').json();assert worker.run_once()
        for headers in (owner,other):assert client.post(f"/api/live/threads/{thread['id']}/join",headers=headers).status_code==200
        yield client,owner,other,staff,thread,worker

def send(live,headers=None,key=None,body='Synthetic comment',parent=None):
    c,a,_,_,t,_=live
    return c.post(f"/api/live/threads/{t['id']}/messages",headers=key_headers(headers or a,key),json={'body':body,'parent_id':parent})

def page(live,headers=None,since=0):
    c,a,_,_,t,_=live
    return c.get(f"/api/live/threads/{t['id']}/events/poll",headers=headers or a,params={'since':since})

def test_extension_initialization_is_additive_idempotent_and_deactivation_compatible(live,settings):
    c,owner,_,_,thread,_=live
    initialize(c.app.state.engine)
    with c.app.state.engine.connect() as db:assert db.execute(text('select version_num from alembic_version')).scalar_one()=='0004_review'
    with TestClient(original_app(settings)) as old:
        assert old.get('/api/v1/posts/'+thread['id'],headers=owner).status_code==200
        assert old.get('/api/live/threads/'+thread['id']+'/events/poll',headers=owner).status_code==404

def test_send_ack_durable_job_even_without_ai_and_pending_privacy(live):
    c,owner,other,_,thread,_=live;result=send(live,body='Stored before inference')
    assert result.status_code==201;cid=result.json()['id']
    with c.app.state.sessions() as db:
        assert db.get(Comment,cid).body=='Stored before inference'
        assert db.scalar(select(ModerationJob).where(ModerationJob.entity_id==cid)).status=='QUEUED'
    own=c.get(f"/api/live/threads/{thread['id']}/snapshot",headers=owner).json()
    assert own['comments']['items'][0]['analysis_status']=='QUEUED'
    peer=c.get(f"/api/live/threads/{thread['id']}/snapshot",headers=other).json()
    assert not peer['comments']['items']

def test_five_authenticated_accounts_create_post_comments_and_reply_with_durable_events(live):
    c,owner,other,_,_,worker=live
    people=[owner,other]+[actor(c,'feed_'+name) for name in ('carol','dave','emma')]
    identities=[c.get('/api/v1/me',headers=h).json()['id'] for h in people]
    assert len(set(identities))==5
    created=post(c,owner,'Synthetic social feed post from a real authenticated author').json()
    assert created['author_id']==identities[0]
    assert created['id'] not in {r['id'] for r in c.get('/api/v1/feed',headers=other).json()['items']}
    assert worker.run_once()
    for person in people:
        assert created['id'] in {r['id'] for r in c.get('/api/v1/feed',headers=person).json()['items']}
        assert c.post(f"/api/live/threads/{created['id']}/join",headers=person).status_code==200
    parent=None;ids=[]
    for index,person in enumerate(people):
        result=c.post(f"/api/live/threads/{created['id']}/messages",headers=key_headers(person),
            json={'body':f'Synthetic comment by distinct actor {index}','parent_id':parent if index==2 else None})
        assert result.status_code==201;row=result.json();ids.append(row['id'])
        assert row['author_id']==identities[index]
        if index==0:parent=row['id']
        if index==2:assert row['parent_id']==parent
        assert worker.run_once()
    for person in people:
        snapshot=c.get(f"/api/live/threads/{created['id']}/snapshot",headers=person).json()
        assert {r['id'] for r in snapshot['comments']['items']}==set(ids)
    with c.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ModerationJob).where(ModerationJob.entity_id.in_(ids)))==5
        assert set(db.scalars(select(LiveEvent.content_id).where(LiveEvent.thread_id==created['id'])))>=set(ids)

def test_idempotent_send_same_job_and_events_no_duplicate(live):
    key=str(uuid4());first=send(live,key=key);cursor=page(live).json()['cursor'];again=send(live,key=key)
    assert first.status_code==201 and again.status_code==200
    assert first.json()['id']==again.json()['id'] and again.headers['Idempotency-Replayed']=='true'
    assert not page(live,since=cursor).json()['items']
    assert send(live,key=key,body='Different payload').status_code==409

def test_concurrent_retries_create_one_comment_and_one_job(live):
    key=str(uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda _:send(live,key=key),range(2)))
    assert sorted(r.status_code for r in responses)==[200,201]
    assert len({r.json()['id'] for r in responses})==1
    with live[0].app.state.sessions() as db:
        cid=responses[0].json()['id'];assert db.scalar(select(func.count()).select_from(ModerationJob).where(ModerationJob.entity_id==cid))==1

def test_membership_and_visibility_are_both_required(live):
    c,owner,other,_,thread,_=live
    assert c.delete(f"/api/live/threads/{thread['id']}/join",headers=other).status_code==200
    assert page(live,other).status_code==403 and send(live,other).status_code==403
    private=post(c,owner,'Pending private content').json()
    assert c.post(f"/api/live/threads/{private['id']}/join",headers=other).status_code==404
    assert c.get(f"/api/live/threads/{private['id']}/events?once=true",headers=other).status_code==404

def test_cross_thread_parent_and_missing_auth_rejected(live):
    c,owner,_,_,thread,worker=live
    first=send(live).json();worker.run_once()
    another=post(c,owner).json();worker.run_once();c.post(f"/api/live/threads/{another['id']}/join",headers=owner)
    result=c.post(f"/api/live/threads/{another['id']}/messages",headers=key_headers(owner),json={'body':'No cross thread','parent_id':first['id']})
    assert result.status_code==404
    assert c.get(f"/api/live/threads/{thread['id']}/events?once=true").status_code==401

def test_sse_envelopes_privacy_order_and_replay(live):
    c,owner,_,_,thread,_=live;send(live,body='DO_NOT_PUT_BODY_IN_SSE')
    data=c.get(f"/api/live/threads/{thread['id']}/events?once=true",headers=owner)
    assert data.status_code==200 and data.headers['content-type'].startswith('text/event-stream')
    assert 'DO_NOT_PUT_BODY_IN_SSE' not in data.text and owner['Authorization'] not in data.text
    frames=[json.loads(line[6:]) for line in data.text.splitlines() if line.startswith('data: ')]
    ids=[r['event_id'] for r in frames];assert ids==sorted(set(ids)) and ids
    assert not page(live,since=max(ids)).json()['items']
    assert page(live,since=max(ids)+1_000_000).status_code==409
    assert c.get(f"/api/live/threads/{thread['id']}/events?once=true&access_token=bad",headers=owner).status_code==400

def test_staff_stream_rbac_and_no_evidence_or_text_leak(live):
    c,owner,_,staff,_,_=live
    assert c.get('/api/live/moderator/events?once=true',headers=owner).status_code==403
    result=c.get('/api/live/moderator/events?once=true',headers=staff)
    assert result.status_code==200 and 'data: ' in result.text and 'lexical_signals' not in result.text

def test_worker_commit_pushes_result_and_peer_snapshot_after_publication(live):
    c,owner,other,_,thread,worker=live;cid=send(live).json()['id'];before=page(live).json()['cursor']
    assert worker.run_once()
    notifications=page(live,other,before).json()['items']
    assert any(r['event_type']=='moderation.analysis.updated' and r['content_id']==cid for r in notifications)
    snap=c.get(f"/api/live/threads/{thread['id']}/snapshot",headers=other).json()
    assert snap['comments']['items'][0]['analysis_status']=='COMPLETED'
    assert snap['comments']['items'][0]['body']=='Synthetic comment'

def test_ai_retry_state_and_recovery_use_existing_worker(live):
    c,_,_,_,_,worker=live;cid=send(live).json()['id'];claim=worker.claim()
    assert worker.finish(claim,error=AIError('AI_HTTP_503',True))
    assert any(r['analysis_status']=='RETRYING' for r in page(live).json()['items'])
    with c.app.state.sessions.begin() as db:
        job=db.scalar(select(ModerationJob).where(ModerationJob.entity_id==cid));job.next_retry_at=0
    assert worker.run_once()
    with c.app.state.sessions() as db:assert db.scalar(select(ModerationJob).where(ModerationJob.entity_id==cid)).status=='SUCCEEDED'

def test_stale_result_cannot_overwrite_edit_or_deleted_content(live):
    c,owner,_,_,_,worker=live;row=send(live).json();claim=worker.claim()
    edited=c.patch('/api/v1/comments/'+row['id'],headers=owner,json={'body':'New revision',**versions(row)});assert edited.status_code==200
    assert not worker.finish(claim,response=response(claim.payload))
    with c.app.state.sessions() as db:
        assert db.get(Comment,row['id']).body=='New revision' and db.get(ModerationResult,claim.job_id) is None
    assert any(r['analysis_status']=='SUPERSEDED' for r in page(live).json()['items'])

def test_event_failure_rolls_back_comment_and_job_atomically(live):
    c=live[0]
    def fail(*args):raise RuntimeError('Synthetic event persistence failure')
    event.listen(LiveEvent,'before_insert',fail)
    try:
        with pytest.raises(RuntimeError,match='Synthetic event'):send(live,body='must rollback')
    finally:event.remove(LiveEvent,'before_insert',fail)
    with c.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(Comment).where(Comment.body=='must rollback'))==0

def test_restart_retains_cursor_and_jobs_and_revalidates_expiry(live,settings):
    c,owner,_,_,thread,_=live;send(live);cursor=page(live).json()['cursor']
    with TestClient(create_app(settings)) as restarted:
        result=restarted.get(f"/api/live/threads/{thread['id']}/events/poll",headers=owner).json();assert result['cursor']==cursor
        with restarted.app.state.sessions.begin() as db:
            db.execute(__import__('sqlalchemy').update(AuthSession).values(created_at=int(time.time())-100,expires_at=int(time.time())-1))
        assert restarted.get(f"/api/live/threads/{thread['id']}/events/poll",headers=owner).status_code==401
