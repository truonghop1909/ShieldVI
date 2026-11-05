"""Threat-driven checks against disposable synthetic accounts and data."""
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
import json
import sqlite3
import threading
import statistics
import time

from fastapi.testclient import TestClient
import httpx
import pytest
from sqlalchemy import select

from shieldvi_social.ai_client import AIClient, AIError, WorkerSettings
from shieldvi_social.backup import create_backup,verify
from shieldvi_social.main import create_app
from shieldvi_social.models import AuthSession, ContentAudit, ModerationJob, Post, User
from shieldvi_social.worker_context import payload_for
from conftest import login
from test_content import actor, comment, post, versions
from test_review import decision, detail_path, path
from test_worker import make_worker, setup


def test_validation_does_not_echo_attacker_controlled_json_keys(client):
    marker = "private-email-in-field-name@example.invalid"
    result = client.post('/api/v1/auth/login',json={'username':'absent','password':'secret-value',marker:'hidden-value'})
    assert result.status_code == 422
    assert marker not in result.text and 'hidden-value' not in result.text and 'secret-value' not in result.text


@pytest.mark.parametrize('reason',['bad\x00reason','bad\ud800reason'])
def test_admin_delete_reason_requires_valid_unicode(authenticated,reason):
    client,owner = authenticated
    admin = actor(client,'fixture_admin','admin')
    row = post(client,owner).json()
    result = client.request('DELETE',f"/api/v1/posts/{row['id']}",headers={**admin,'Content-Type':'application/json'},
        content=json.dumps({**versions(row),'reason':reason}))
    assert result.status_code == 422
    assert client.get(f"/api/v1/posts/{row['id']}",headers=owner).json()['visibility_status'] == 'PENDING_MODERATION'


def test_cookie_and_forged_jwt_do_not_authenticate_or_mutate(authenticated):
    client,headers = authenticated
    token = headers['Authorization'].removeprefix('Bearer ')
    row = post(client,headers).json()
    with TestClient(client.app) as cross_site:
        cross_site.cookies.set('access_token',token)
        for bearer in (None,'Bearer eyJhbGciOiJub25lIn0.eyJyb2xlIjoiYWRtaW4ifQ.'):
            sent = {'Origin':'https://attacker.invalid',**({'Authorization':bearer} if bearer else {})}
            result = cross_site.request('DELETE',f"/api/v1/posts/{row['id']}",headers=sent,json=versions(row))
            assert result.status_code == 401
        assert cross_site.get('/api/v1/me?access_token='+token).status_code == 401
    assert client.get(f"/api/v1/posts/{row['id']}",headers=headers).json()['visibility_status'] == 'PENDING_MODERATION'


@pytest.mark.parametrize('origin',['http://localhost:5173.attacker.invalid','null','https://attacker.invalid'])
def test_cors_exact_match_rejects_mutation_preflight(client,origin):
    response=client.options('/api/v1/moderation/decisions',headers={'Origin':origin,
        'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'authorization,content-type'})
    assert response.status_code==400
    assert 'access-control-allow-origin' not in response.headers
    assert 'access-control-allow-credentials' not in response.headers


def test_cors_allowed_mutation_and_security_headers(authenticated):
    client,headers=authenticated
    response=client.options('/api/v1/moderation/decisions',headers={'Origin':'http://localhost:5173',
        'Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'authorization,content-type'})
    assert response.status_code==200 and response.headers['access-control-allow-origin']=='http://localhost:5173'
    for response in (client.get('/api/v1/me',headers=headers),client.get('/api/v1/moderation/queue'),
                     client.post('/api/v1/auth/login',json={})):
        assert response.headers['cache-control']=='no-store'
        assert response.headers['x-content-type-options']=='nosniff'
        assert 'set-cookie' not in response.headers


def test_revocation_role_downgrade_and_suspend_all_staff_reads(authenticated):
    client,author=authenticated
    staff=actor(client,'fixture_staff','moderator')
    row=post(client,author).json()
    routes=['/api/v1/moderation/queue','/api/v1/moderation/jobs',detail_path(row),detail_path(row)+'/audit']
    for route in routes:assert client.get(route,headers=staff).status_code==200
    with client.app.state.sessions.begin() as db:
        user=db.scalar(select(User).where(User.username=='fixture_staff'));user.role='user'
    for route in routes:assert client.get(route,headers=staff).status_code==403
    with client.app.state.sessions.begin() as db:
        db.scalar(select(User).where(User.username=='fixture_staff')).status='suspended'
    for route in routes:assert client.get(route,headers=staff).status_code==401


def test_report_and_appeal_share_durable_mutation_rate_limit(authenticated,settings):
    client,author=authenticated
    staff=actor(client,'fixture_staff','moderator');viewer=actor(client,'fixture_viewer')
    row=decision(client,staff,post(client,author).json(),'approve').json()
    with TestClient(create_app(replace(settings,content_rate_limit=1))) as limited:
        payload={**versions(row),'reason':'Synthetic reason'}
        assert limited.post(path(row)+'/reports',headers=viewer,json=payload).status_code==200
        assert limited.post(path(row)+'/reports',headers=viewer,json=payload).status_code==429
    hidden=decision(client,staff,row,'hide').json()
    with TestClient(create_app(replace(settings,content_rate_limit=1))) as limited:
        # Author already created a post in this same persisted rate window.
        assert limited.post(path(row)+'/appeals',headers=author,json={**versions(hidden),'reason':'Review'}).status_code==429


def test_worker_payload_minimizes_identity_and_omits_deleted_context(authenticated,caplog):
    client,headers=authenticated
    marker='SYNTHETIC_PII_TEXT_MARKER_019'
    parent=post(client,headers,body=marker).json()
    row=comment(client,headers,parent['id'],body='Current synthetic text').json()
    with client.app.state.sessions() as db:
        from shieldvi_social.models import Comment
        item=db.get(Comment,row['id'])
        job=db.scalar(select(ModerationJob).where(ModerationJob.entity_id==item.id))
        payload=payload_for(db,job,item).model_dump(mode='json')
        assert set(payload)=={'schema_version','request_id','content_id','content_type','content_revision','user_id','text',
            'timestamp','parent_id','mentioned_user_ids','context','language_hint'}
        serialized=json.dumps(payload)
        assert 'fixture@example.com' not in serialized and 'synthetic-test-password' not in serialized
        assert headers['Authorization'] not in serialized
        assert 'username' not in serialized and 'password_hash' not in serialized and 'ip_address' not in serialized
        assert payload['context']['complete'] is False
        assert len(payload['context']['recent_comments'])<=50
    assert marker not in caplog.text and headers['Authorization'] not in caplog.text


def test_http_request_and_ai_error_logs_contain_no_pii_or_tokens(setup,caplog):
    client,headers,row,_,_=setup
    marker='SYNTHETIC_PRIVATE_CONTENT_019'
    row=post(client,headers,body=marker).json()
    worker=make_worker(setup,lambda _: (_ for _ in ()).throw(AIError('AI_TIMEOUT',True)))
    assert worker.run_once()
    client.get(f"/api/v1/posts/{row['id']}",headers=headers)
    client.post('/api/v1/auth/login',json={'username':'unknown','password':marker})
    assert marker not in caplog.text
    assert headers['Authorization'] not in caplog.text and 'fixture@example.com' not in caplog.text


def test_sqlite_online_backup_restores_content_jobs_audit_and_session(authenticated,tmp_path):
    client,headers=authenticated
    row=post(client,headers,body='Synthetic backup fixture').json()
    source=client.app.state.engine.url.database
    backup=tmp_path/'social-backup.sqlite3'
    # Online backup API copies committed transactions; no file overwrite of source.
    assert create_backup(client.app.state.settings,backup)=={'integrity':'ok','foreign_keys':'ok','schema':'0004_review'}
    with TestClient(create_app(replace(client.app.state.settings,database_url='sqlite:///'+backup.as_posix()))) as restored:
        assert restored.get('/api/v1/me',headers=headers).status_code==200
        assert restored.get(f"/api/v1/posts/{row['id']}",headers=headers).json()['body']=='Synthetic backup fixture'
        with restored.app.state.sessions() as db:
            assert db.scalar(select(ModerationJob).where(ModerationJob.entity_id==row['id'])) is not None
            assert db.scalar(select(ContentAudit).where(ContentAudit.entity_id==row['id'])) is not None


def test_backup_refuses_existing_output_and_source_alias(client,tmp_path):
    destination=tmp_path/'existing.sqlite3';destination.write_bytes(b'preserve-existing-backup')
    with pytest.raises(FileExistsError):create_backup(client.app.state.settings,destination)
    assert destination.read_bytes()==b'preserve-existing-backup'
    with pytest.raises(ValueError,match='must differ'):
        create_backup(client.app.state.settings,client.app.state.engine.url.database)


def test_backup_supports_pre_upgrade_schema_and_never_restores(client,tmp_path):
    backup=tmp_path/'historical.sqlite3'
    create_backup(client.app.state.settings,backup)
    with sqlite3.connect(backup) as db:db.execute("UPDATE alembic_version SET version_num='0002_content'")
    assert verify(backup)['schema']=='0002_content'
    assert client.get('/health').status_code==200


def test_login_does_not_upgrade_deferred_read_into_competing_worker_write(authenticated,monkeypatch):
    client,headers=authenticated
    row=post(client,headers).json()
    from shieldvi_social import routes
    original=routes.verify_password
    read=threading.Event();writer=threading.Event()
    def verify_after_read(*args):
        read.set();writer.wait(.25)
        return original(*args)
    monkeypatch.setattr(routes,'verify_password',verify_after_read)
    def worker_write():
        assert read.wait(5)
        with client.app.state.sessions.begin() as db:
            db.connection(execution_options={'sqlite_immediate':True})
            writer.set();db.get(Post,row['id']).policy_version='concurrency-fixture'
    with ThreadPoolExecutor(2) as pool:
        background=pool.submit(worker_write)
        result=pool.submit(login,client).result(timeout=10)
        background.result(timeout=10)
    assert result.status_code==200


def test_sqlalchemy_tracebacks_hide_bound_parameters(client):
    assert client.app.state.engine.hide_parameters is True


def test_authenticated_queue_metrics_do_not_block_worker_commits(setup):
    client,author,row,_,_=setup
    staff=actor(client,'fixture_metrics_staff','moderator')
    for index in range(8):assert post(client,author,body=f'Concurrent metrics fixture {index}').status_code==201
    worker=make_worker(setup)
    def process():
        for _ in range(9):assert worker.run_once()
    def read_metrics():
        for _ in range(25):assert client.get('/api/v1/moderation/jobs',headers=staff).status_code==200
    with ThreadPoolExecutor(2) as pool:
        writes=pool.submit(process);reads=pool.submit(read_metrics)
        writes.result(timeout=30);reads.result(timeout=30)
    with client.app.state.sessions() as db:
        assert len(db.scalars(select(Post).where(Post.visibility_status=='PUBLISHED')).all())==9


def test_large_feed_fixture_pagination_privacy_and_latency(authenticated,record_testsuite_property):
    client,headers=authenticated
    with client.app.state.sessions.begin() as db:
        owner=db.scalar(select(User))
        now=int(time.time())
        for index in range(1200):
            public=index<1000
            state='PUBLISHED' if public else ['PENDING_MODERATION','HELD_FOR_REVIEW','HIDDEN','DELETED_BY_AUTHOR'][index%4]
            db.add(Post(author_id=owner.id,body=f'{"PUBLIC" if public else "PRIVATE"}-SYNTHETIC-FEED-{index}',
                create_key=f'large-feed-{index}',request_hash='synthetic',visibility_status=state,created_at=now-index))
    ids=set();durations=[]
    for page in range(1,21):
        start=time.perf_counter()
        response=client.get(f'/api/v1/feed?page={page}&page_size=50',headers=headers)
        durations.append((time.perf_counter()-start)*1000)
        assert response.status_code==200
        body=response.json()
        assert body['total']==1000 and len(body['items'])==50
        assert 'PRIVATE-SYNTHETIC-FEED' not in response.text
        ids.update(row['id'] for row in body['items'])
    assert len(ids)==1000
    assert client.get('/api/v1/feed?page=21&page_size=50',headers=headers).json()['items']==[]
    record_testsuite_property('synthetic_feed_public_rows',1000)
    record_testsuite_property('synthetic_feed_private_rows',200)
    record_testsuite_property('synthetic_feed_20_reads_median_ms',round(statistics.median(durations),3))
    record_testsuite_property('synthetic_feed_20_reads_p95_ms',round(sorted(durations)[18],3))
