from datetime import datetime,timedelta,timezone
from pathlib import Path
import pytest
from app.live_analysis import IncrementalAnalyzer
from app.moderation_contract import ModerationRequest

class FakePredictor:
    threshold=.41;name='unit_fake_scores_not_neural_metrics'
    def __init__(self):self.texts=0
    def predict_scores(self,texts):
        self.texts+=len(texts)
        return [.9 if 'ngu' in text.lower() or 'vô dụng' in text.lower() else .02 for text in texts]

def row(cid,user,text,parent=None,minute=0):
    return {'comment_id':cid,'user_id':user,'text':text,'parent_id':parent,'timestamp':datetime(2026,11,4,tzinfo=timezone.utc)+timedelta(minutes=minute)}

def request(current,context=(),revision=1):
    return ModerationRequest.model_validate({'schema_version':'1.0','request_id':'req_'+current['comment_id'],
        'content_id':current['comment_id'],'content_type':'comment','content_revision':revision,'user_id':current['user_id'],
        'text':current['text'],'timestamp':current['timestamp'],'parent_id':current.get('parent_id'),
        'context':{'post_id':'thread','source':'social-api','complete':False,'recent_comments':list(context)}})

def analyzer():return IncrementalAnalyzer(FakePredictor(),fingerprint='a'*64)

def test_three_messages_only_three_neural_texts_and_grounded_repeated():
    a=row('a','A','Mình gửi lịch mới.');b=row('b','B','Mày đúng là đồ ngu.','a',1);c=row('c','B','Mày là đồ vô dụng.','a',2)
    engine=analyzer();first=engine.analyze(request(a));second=engine.analyze(request(b,[a]));third=engine.analyze(request(c,[a,b]))
    assert [r.conversation_signals.neural_texts for r in (first,second,third)]==[1,1,1]
    assert engine.predictor.texts==3 and third.suspected_repeated_harassment
    assert third.evidence[0].evidence_comment_ids==['b','c'] and third.evidence[0].target_user_id=='A'
    assert third.conversation_signals.processor=='default-v5' and third.conversation_signals.current.directed_at_user_id=='A'

@pytest.mark.parametrize('text',[
    'Tôi xin lỗi vì đã gọi bạn là đồ ngu.',
    'Đừng gọi bạn ấy là đồ ngu.',
    'Mình bị chửi như vậy nên rất buồn.',
    'Đm máy hết pin rồi, mình chưa lưu bài.',
])
def test_apology_intervention_defense_or_profanity_not_new_instances(text):
    a=row('a','A','Mình gửi lịch mới.');b=row('b','B',text,'a',1)
    result=analyzer().analyze(request(b,[a]))
    assert not result.conversation_signals.current.attack_instance_candidate and not result.evidence

def test_two_actors_and_mutual_attack_do_not_merge():
    a=row('a','A','Bản thiết kế mới.');b=row('b','B','Bạn đúng là đồ ngu.','a',1);c=row('c','C','Mày vô dụng.','a',2)
    result=analyzer().analyze(request(c,[a,b]));assert not result.evidence
    d=row('d','A','Mày đúng là đồ ngu.','b',3)
    assert not analyzer().analyze(request(d,[a,b])).evidence

def test_plain_reply_is_recipient_not_attack_target():
    a=row('a','A','Mình gửi lịch mới.');b=row('b','B','Bạn thêm giờ bắt đầu nhé.','a',1)
    result=analyzer().analyze(request(b,[a]));sig=result.conversation_signals.current
    assert sig.reply_to_user_id=='A' and sig.directed_at_user_id is None and not sig.attack_instance_candidate

def test_edit_invalidates_changed_text_only_and_recomputes_context():
    engine=analyzer();a=row('a','A','Bản mới.');b=row('b','B','Mày ngu.','a',1);c=row('c','B','Mày vô dụng.','a',2)
    engine.analyze(request(c,[a,b]));b['text']='Mình hiểu rồi, cảm ơn bạn.'
    changed=engine.analyze(request(c,[a,b]))
    assert changed.conversation_signals.neural_texts==1 and not changed.evidence

def test_horizon_does_not_include_old_attack_as_repeated():
    a=row('a','A','Bản mới.');b=row('b','B','Mày ngu.','a',1);c=row('c','B','Mày vô dụng.','a',40)
    result=analyzer().analyze(request(c,[a,b]));assert not result.evidence

def test_reordered_future_context_is_rejected_before_inference():
    a=row('a','A','Future',minute=3);b=row('b','B','Mày ngu.',minute=1)
    with pytest.raises(ValueError):request(b,[a])

def test_model_unavailable_never_creates_fake_raw_score():
    engine=analyzer();engine.predictor.predict_scores=lambda texts: (_ for _ in ()).throw(RuntimeError('offline'))
    with pytest.raises(RuntimeError):engine.analyze(request(row('a','A','Hello')))
    assert not engine.cache

def test_experimental_processor_requires_explicit_shadow_and_contracts_are_identical():
    with pytest.raises(ValueError):IncrementalAnalyzer(FakePredictor(),'a'*64,processor='experimental-v6.2')
    root=Path(__file__).resolve().parents[1]
    assert (root/'services/moderation-ai/app/live_analysis_contract.py').read_bytes()==(root/'services/social-api/src/shieldvi_social/live_analysis_contract.py').read_bytes()

def test_opt_in_factory_does_not_mutate_default_app_routes():
    from app import main
    from app.live_entrypoint import create_app
    before=[getattr(route,'path',None) for route in main.app.routes];live=create_app()
    assert '/api/live/moderate/comment' in live.openapi()['paths']
    assert [getattr(route,'path',None) for route in main.app.routes]==before

def test_report_gate_keeps_new_attack_outside_quote_and_preserves_base_fields():
    a=row('a','A','Bản mới.')
    report=row('b','B','Tôi xin lỗi vì đã gọi bạn là đồ ngu.','a',1)
    result=analyzer().analyze(request(report,[a]));current=result.conversation_signals.current
    assert current.base_attack_instance_candidate and not current.attack_instance_candidate
    assert current.instance_gate_reason=='reported_predicate_only' and result.ai_label=='TOXIC'
    new=row('b','B','Tôi xin lỗi vì đã gọi bạn là đồ ngu, nhưng mày vẫn vô dụng.','a',1)
    assert analyzer().analyze(request(new,[a])).conversation_signals.current.attack_instance_candidate

def test_live_http_auth_body_limit_and_validation_redaction(monkeypatch):
    from fastapi.testclient import TestClient
    from app.live_entrypoint import create_app
    from app import main
    token='unit-only-service-token-length-at-least32'
    monkeypatch.setenv('AI_SERVICE_TOKEN',token);monkeypatch.setenv('AI_SERVICE_RATE_LIMIT','1000')
    app=create_app();fake=FakePredictor();app.dependency_overrides[main.get_predictor]=lambda:fake
    app.state.live_analyzers[id(fake)]=IncrementalAnalyzer(fake,'a'*64)
    client=TestClient(app);payload=request(row('a','A','Synthetic body')).model_dump(mode='json')
    assert client.post('/api/live/moderate/comment',json=payload).status_code==401
    headers={'Authorization':'Bearer '+token}
    assert client.post('/api/live/moderate/comment',headers=headers,json=payload).status_code==200
    bad=client.post('/api/live/moderate/comment',headers=headers,json={**payload,'secret_text':'NO_ECHO_PRIVATE'})
    assert bad.status_code==422 and 'NO_ECHO_PRIVATE' not in bad.text
    assert client.post('/api/live/moderate/comment',headers=headers,content=b' '*1048577).status_code==413
