import json,secrets,time,threading
from pathlib import Path
import pytest
from pydantic import ValidationError
from sqlalchemy import select,func
from test_live_api import live
from test_live_analysis_worker import FixtureAI
from test_content import actor
from shieldvi_social.live_quick_test import QuickConversation,QuickTests
from shieldvi_social.ai_client import AIError
from shieldvi_social.models import Post,Comment,ModerationJob,ModerationResult

BASE='/api/live/moderator/test-conversations'
def payload():return {'thread_id':'QUICK_UNIT','comments':[
    {'comment_id':'c1','user_id':'A','text':'Mình chia sẻ lịch sinh hoạt.','timestamp':'2026-11-05T01:00:00Z'},
    {'comment_id':'c2','user_id':'B','parent_id':'c1','text':'Mình đồng ý, cảm ơn bạn.','timestamp':'2026-11-05T01:01:00Z'}]}

def configure(live,monkeypatch,factory=None):
    monkeypatch.setenv('SOCIAL_AI_SERVICE_TOKEN',secrets.token_urlsafe(32))
    live[0].app.state.quick_tests=QuickTests(client_factory=factory or (lambda _:FixtureAI()))
    return live[0].app.state.quick_tests

def finished(c,headers,identity):
    deadline=time.monotonic()+4
    while time.monotonic()<deadline:
        result=c.get(BASE+'/'+identity,headers=headers).json()
        if result['status'] not in ('QUEUED','RUNNING','CANCELLING'):return result
        time.sleep(.01)
    raise AssertionError('Unit test job did not terminate')

def test_staff_only_and_owner_private_results_without_content_writes(live,monkeypatch):
    c,owner,_,staff,_,_=live;configure(live,monkeypatch)
    assert c.post(BASE,json=payload()).status_code==401
    assert c.post(BASE,headers=owner,json=payload()).status_code==403
    with c.app.state.sessions() as db:before=[db.scalar(select(func.count()).select_from(m)) for m in (Post,Comment,ModerationJob,ModerationResult)]
    response=c.post(BASE,headers=staff,json=payload());assert response.status_code==202
    identity=response.json()['id'];job=finished(c,staff,identity);assert job['status']=='COMPLETED'
    result=job['result'];assert result['threshold']==.41 and result['processor']=='default-v5' and result['content_saved'] is False
    current=result['comments'][1]['analysis']['conversation_signals']['current']
    assert current['reply_to_user_id']=='A' and not current['attack_instance_candidate'] and current['directed_at_user_id'] is None
    another=actor(c,'quick_other_staff','moderator')
    assert c.get(BASE+'/'+identity,headers=another).status_code==404
    assert c.get(BASE+'/'+identity,headers=owner).status_code==403
    with c.app.state.sessions() as db:after=[db.scalar(select(func.count()).select_from(m)) for m in (Post,Comment,ModerationJob,ModerationResult)]
    assert before==after

@pytest.mark.parametrize('change',['duplicate','missing_parent','future_parent','naive_time','oversize','threshold','research_profile'])
def test_invalid_json_graph_or_override_rejected(change):
    value=payload()
    if change=='duplicate':value['comments'][1]['comment_id']='c1'
    if change=='missing_parent':value['comments'][1]['parent_id']='unknown'
    if change=='future_parent':value['comments'].reverse()
    if change=='naive_time':value['comments'][0]['timestamp']='2026-11-05T01:00:00'
    if change=='oversize':value['comments']=value['comments']*26
    if change=='threshold':value['threshold']=.2
    if change=='research_profile':value['profile']='research_synthetic'
    with pytest.raises(ValidationError):QuickConversation.model_validate(value)

def test_cancel_and_busy_bound_single_background_job(live,monkeypatch):
    started=threading.Event();release=threading.Event()
    class Blocked(FixtureAI):
        def moderate(self,request):started.set();release.wait(3);return super().moderate(request)
    c,_,_,staff,_,_=live;configure(live,monkeypatch,lambda _:Blocked())
    try:
        response=c.post(BASE,headers=staff,json=payload());assert response.status_code==202 and started.wait(1)
        assert c.post(BASE,headers=staff,json=payload()).status_code==429
        identity=response.json()['id'];assert c.delete(BASE+'/'+identity,headers=staff).json()['status']=='CANCELLING'
    finally:release.set()
    assert finished(c,staff,identity)['status']=='CANCELLED'

def test_ai_offline_is_failed_not_clean_and_input_error_does_not_echo_text(live,monkeypatch):
    class Offline:
        def moderate(self,_):raise AIError('AI_NETWORK_ERROR',True)
    c,_,_,staff,_,_=live;configure(live,monkeypatch,lambda _:Offline())
    identity=c.post(BASE,headers=staff,json=payload()).json()['id'];job=finished(c,staff,identity)
    assert job['status']=='FAILED' and job['error']=='AI_NETWORK_ERROR' and job['result'] is None
    data=payload();data['comments'][0]['text']='DO_NOT_ECHO_PRIVATE_TEST';data['comments'][0]['timestamp']='bad'
    response=c.post(BASE,headers=staff,json=data);assert response.status_code==422 and 'DO_NOT_ECHO_PRIVATE_TEST' not in response.text

def test_request_schema_export_matches():
    path=Path(__file__).resolve().parents[3]/'contracts/admin_quick_conversation.schema.json'
    assert json.loads(path.read_text(encoding='utf-8'))==QuickConversation.model_json_schema()
