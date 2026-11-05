"""Runtime/gate diagnostics; passing these tests does NOT resolve NOV10 misses."""
import csv,json
from datetime import datetime
from pathlib import Path
import pytest
from scripts.audit_nov10 import replay
from app.schemas import AnalyzeRequest,AnalyzeResponseV2
from app.experiments.fresh10_v6 import analyze_thread_v6,context_v6
R=Path(__file__).resolve().parents[1];D=R/'datasets/fixtures/nov10_regression_v1'

def case(number):
    payload=json.loads(next((D/'inputs').glob('TEST'+str(number)+'_*.json')).read_text(encoding='utf-8'))
    exported=json.loads(next((D/'analysis').glob('*_'+str(number)+'_*analysis.json')).read_text(encoding='utf-8'))
    return payload,exported

@pytest.mark.parametrize('number',range(11,21))
def test_exact_v61_wire_replay_of_original_export(number):
    payload,exported=case(number);internal,wire=replay(payload,exported)
    assert wire==exported
    assert internal['rule_versions']['context']=='context-v6.1-research'
    assert len(internal['comments'])==20

@pytest.mark.parametrize('number,cid',[(12,'c06'),(15,'c07'),(15,'c12'),(20,'c11')])
def test_documented_raw_toxic_gate_abstention_is_not_runtime_field_loss(number,cid):
    payload,exported=case(number);internal,wire=replay(payload,exported)
    row=next(c for c in internal['comments'] if c['comment_id']==cid)
    assert row['moderation_assessment']['label']=='TOXIC'
    assert row['moderation_assessment']['basis']=='raw_model_fallback'
    assert row['toxicity_score']>=.41
    assert not row['analysis_signals']['research_trace']['matches']
    assert not row['analysis_signals']['context']['attack_candidate']
    assert row['analysis_signals']['target_evidence']['method']=='non_attack_or_uncertain'
    assert not row['analysis_signals']['attack_instance_candidate'] and row['directed_at_user_id'] is None
    assert next(c for c in wire['comments'] if c['comment_id']==cid)['analysis_signals']['directed_attack_candidate'] is False

def positive_control():
    payload=AnalyzeRequest.model_validate({'thread_id':'runtime_control','comments':[
        {'comment_id':'a','user_id':'A','text':'Mình gửi lịch trực mới cho nhóm.','timestamp':'2026-11-04T00:00:00Z'},
        {'comment_id':'b','parent_id':'a','user_id':'B','text':'Bạn đúng là đồ ngu.','timestamp':'2026-11-04T00:02:00Z'},
        {'comment_id':'c','parent_id':'b','user_id':'C','text':'Đừng công kích người khác, hãy nói về lịch trực.','timestamp':'2026-11-04T00:04:00Z'},
        {'comment_id':'d','parent_id':'a','user_id':'B','text':'Mày là đồ vô dụng.','timestamp':'2026-11-04T00:06:00Z'},
        {'comment_id':'e','parent_id':'d','user_id':'B','text':'Tôi xin lỗi vì đã gọi bạn là đồ ngu.','timestamp':'2026-11-04T00:08:00Z'}]})
    class LowScore:
        threshold=.41;name='diagnostic_fake_raw_scores_not_classifier_metrics'
        def predict_scores(self,texts):return [.02]*len(texts)
    return analyze_thread_v6(payload,LowScore())

def test_positive_controls_prove_context_target_instance_repeated_pipeline_runs():
    out=positive_control();rows={c['comment_id']:c for c in out['comments']}
    assert out['evidence'][0]['actor_user_id']=='B' and out['evidence'][0]['target_user_id']=='A'
    assert out['evidence'][0]['evidence_comment_ids']==['b','d']
    assert rows['b']['directed_at_user_id']=='A' and rows['d']['analysis_signals']['attack_instance_candidate']
    assert not rows['c']['analysis_signals']['attack_instance_candidate']
    assert not rows['e']['analysis_signals']['attack_instance_candidate']

def test_v2_serialization_removes_uncontracted_trace_but_keeps_true_attack_fields():
    internal=positive_control();wire=AnalyzeResponseV2.model_validate(internal).model_dump(mode='json')
    a=internal['comments'][1]['analysis_signals'];b=wire['comments'][1]['analysis_signals']
    assert a['research_trace']['matches'] and 'research_trace' not in b
    assert b['directed_attack_candidate'] and b['attack_instance_candidate']
    assert wire['comments'][1]['directed_at_user_id']=='A'

@pytest.mark.parametrize('number',[11,12,14,15,16,18,19,20])
def test_reference_events_have_distinct_times_correct_actor_target_and_no_time_excuse(number):
    payload,_=case(number);by_id={c['comment_id']:c for c in payload['comments']}
    events=list(csv.DictReader((D/'expected_repeated_events.csv').open(encoding='utf-8-sig')))
    event=next(e for e in events if e['thread_id']==payload['thread_id'])
    refs=list(csv.DictReader((D/'expected_reference_labels.csv').open(encoding='utf-8-sig')))
    refs={r['comment_id']:r for r in refs if r['thread_id']==payload['thread_id']}
    ids=event['evidence_comment_ids'].split(';');times=[]
    for cid in ids:
        assert by_id[cid]['user_id']==event['actor_user_id']
        assert refs[cid]['directed_at_user_id']==event['target_user_id'] and refs[cid]['expected_label']=='TOXIC'
        times.append(datetime.fromisoformat(by_id[cid]['timestamp'].replace('Z','+00:00')))
    assert len(set(times))>=2 and 10<=(max(times)-min(times)).total_seconds()/60<=20

@pytest.mark.parametrize('text',[
    'Bài viết nên thêm số liệu đối chiếu để lập luận rõ hơn.',
    'Tôi đã nói “đồ ngu” hôm qua và giờ xin lỗi bạn về lời đó.',
])
def test_no_blanket_attack_for_criticism_or_reported_abuse(text):
    assert not context_v6(text,{'A','B','C'})[0].attack_candidate
