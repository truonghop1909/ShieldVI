"""Frozen synthetic r06 failures; references never derived from predictions."""
import json
from pathlib import Path
from datetime import datetime,timedelta,timezone
import pytest
from app.schemas import AnalyzeRequest
from app.signal_engine import analyze_thread_v2
from app.engine import analyze_thread

R=Path(__file__).resolve().parents[1]
P=R/'reports/ai_update/repeated_recovery_20261103'
EVENTS=json.loads((P/'five_events_before.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('event',EVENTS,ids=[e['thread_id'] for e in EVENTS])
def test_five_frozen_r06_repeated_events(event):
    t=json.loads((R/'datasets/synthetic_genz/threads'/(event['thread_id']+'.json')).read_text(encoding='utf-8'))
    predictions=json.loads((R/'reports/ai_update/synthetic_experiment_r06_20261103/evaluation/predictions.json').read_text(encoding='utf-8'))
    scores={r['text']:r['raw_score'] for r in predictions if r['model']=='r06' and r['thread_id']==t['thread_id']}
    class Cached:
        threshold=.41;name='r06_actual_scores_cached'
        def predict_scores(self,texts):return [scores[text] for text in texts]
    payload={'thread_id':t['thread_id'],'comments':[{k:c[k] for k in ('comment_id','user_id','parent_id','timestamp','text')} for c in t['comments']]}
    parsed=AnalyzeRequest.model_validate(payload)
    out=analyze_thread_v2(parsed,Cached())
    legacy={c['comment_id']:c for c in analyze_thread(parsed,Cached()).model_dump(mode='json')['comments']}
    pairs=[e for e in out['evidence'] if (e['actor_user_id'],e['target_user_id'])==(event['actor'],event['target'])]
    assert len(pairs)==1
    assert pairs[0]['evidence_comment_ids']==event['reference_ids']
    for row in out['comments']:
        # Legacy serializes scores to six decimals; compare the actual invariant
        # fields rather than demanding unrounded cache floats in the API.
        for field in ('toxicity_score','toxic_for_moderation','toxic_for_repeated_rule','target_user_id','target_method','target_confidence','lexical_signals'):
            assert row[field]==legacy[row['comment_id']][field]

def run_rows(rows):
    now=datetime(2026,11,3,tzinfo=timezone.utc)
    class Low:
        name='UNIT_MOCK_ONLY';threshold=.41
        def predict_scores(self,texts):return [.02]*len(texts)
    payload=AnalyzeRequest(thread_id='unseen_ids',comments=[{'comment_id':cid,'user_id':user,'parent_id':parent,'text':text,'timestamp':now+timedelta(minutes=i)} for i,(cid,user,parent,text) in enumerate(rows)])
    return analyze_thread_v2(payload,Low())

@pytest.mark.parametrize('text',[
    'Bạn đừng bảo người ta ngậm miệng đi.',
    'Mình xin lỗi vì đã nói mày chẳng có chút giá trị gì.',
    'Tôi trích dẫn “có mày hay không cũng chẳng ai cần” để phản đối.',
    'Bạn không hề vô giá trị.',
    'Mình muốn câm hẳn đi một lúc cho đỡ mệt.',
    'Mày chỉnh mic đi thì đỡ vang.',
    'Trong bài tập thở, mày ngậm miệng lại để thở bằng mũi.',
])
def test_non_attack_forms_do_not_create_new_instances(text):
    out=run_rows([('p','victim',None,'Mình muốn góp ý.'),('a','actor','p',text),('b','actor','p',text)])
    assert not out['evidence']
    assert not any(c['analysis_signals']['attack_instance_candidate'] for c in out['comments'])

def test_unanswered_root_attack_must_still_abstain():
    out=run_rows([('a','actor',None,'Mày ngu thật.'),('v','victim',None,'Bài mới của mình.'),('b','actor','v','Mày vô dụng.')])
    assert not out['evidence']
    assert out['comments'][0]['directed_at_user_id'] is None

def test_intervention_reply_does_not_establish_root_attack_target():
    out=run_rows([('a','actor',None,'Mày ngu thật.'),('i','helper','a','Đừng gọi bạn ấy ngu.'),('v','victim',None,'Mình sẽ kiểm tra lại nguồn.'),('b','actor','v','Mày vô dụng.')])
    assert not out['evidence']
    assert out['comments'][0]['directed_at_user_id'] is None

def test_conflicting_later_targets_do_not_backfill_root_attack():
    out=run_rows([('a','actor',None,'Mày ngu thật.'),('r','victim','a','Mình sẽ kiểm lại nguồn.'),
        ('b','actor','r','Mày vô dụng.'),('v','other',None,'Mình đang xem.'),('c','actor','v','other mày ngu thật.')])
    assert out['comments'][0]['directed_at_user_id'] is None
    assert not out['evidence']

def test_apology_followed_by_new_disparagement_still_forms_attack_instance():
    out=run_rows([('p','victim',None,'Bài của mình.'),('a','actor','p','Xin lỗi vì đã nói nặng, nhưng mày chẳng có chút giá trị gì.'),
        ('b','actor','p','Có mày hay không cũng chẳng ai cần.')])
    assert out['evidence'][0]['evidence_comment_ids']==['a','b']
