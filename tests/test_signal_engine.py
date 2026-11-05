import json
from pathlib import Path
from app.schemas import AnalyzeRequest
from app.signal_engine import analyze_thread_v2
from app.engine import analyze_thread
class Model:
    name='MOCK_ONLY';threshold=.41
    def predict_scores(self,texts):return [.9]*len(texts)
def conversation(texts,times=None):
    rows=[{'comment_id':'root','user_id':'A','timestamp':'2026-01-01T00:00:00Z','text':'Bài mới của mình'}]
    for i,t in enumerate(texts):rows.append({'comment_id':f'x{i}','user_id':'B','parent_id':'root','timestamp':times[i] if times else f'2026-01-01T00:{i+1:02d}:00Z','text':t})
    return AnalyzeRequest(thread_id='different_ids',comments=rows)
def test_apology_after_attacks_does_not_remove_history_or_add_attack():
    p=conversation(['Mày ngu thật.','Mày vô dụng.','Mình xin lỗi vì đã gọi bạn ngu.'])
    out=analyze_thread_v2(p,Model());assert out['evidence'][0]['evidence_comment_ids']==['x0','x1']
    assert out['evidence'][0]['target_user_id']=='A'
    assert out['comments'][-1]['toxic_for_moderation'] and not out['comments'][-1]['analysis_signals']['attack_instance_candidate']
def test_quote_only_or_apology_only_cannot_create_repeated():
    for texts in [['Mình xin lỗi vì đã gọi bạn ngu.']*2,['Tôi trích dẫn “mày ngu” để phản đối.']*2]:
        assert not analyze_thread_v2(conversation(texts),Model())['evidence']
def test_mixed_apology_attack_still_counts():
    out=analyze_thread_v2(conversation(['Xin lỗi nhưng mày vẫn ngu.','Mày vô dụng.']),Model())
    assert out['suspected_repeated_harassment']
def test_same_timestamp_not_repeated():
    p=conversation(['Mày ngu.','Mày vô dụng.'],['2026-01-01T00:01:00Z']*2)
    assert not analyze_thread_v2(p,Model())['evidence']
def test_raw_scores_labels_and_recipient_fields_remain_unchanged():
    p=conversation(['Mình xin lỗi vì đã gọi bạn ngu.']*2)
    a=analyze_thread(p,Model()).model_dump(mode='json');b=analyze_thread_v2(p,Model())
    for old,new in zip(a['comments'],b['comments']):
        for field in ('toxicity_score','toxic_for_moderation','toxic_for_repeated_rule','target_user_id','target_method','target_confidence'):assert old[field]==new[field]
    assert b['policy_executed'] is False

def test_game_developer_chain_has_no_recovery_turns_in_evidence():
    root=Path(__file__).resolve().parents[1]
    p=AnalyzeRequest.model_validate(json.loads(next((root/'datasets/fixtures/genz_regression').glob('*GAME*.json')).read_text(encoding='utf-8')))
    out=analyze_thread_v2(p,Model())
    chain=next(e for e in out['evidence'] if e['actor_user_id']=='U02' and e['target_user_id']=='U03')
    assert {'c08','c11','c15','c18'}<=set(chain['evidence_comment_ids'])
    assert not {'c12','c16','c23','c24'}&set(chain['evidence_comment_ids'])
