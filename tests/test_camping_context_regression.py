"""Camping references are synthetic, not human gold; raw scores are real API caches."""
import copy,json,re,sys,unicodedata
from pathlib import Path
import pytest
from app.schemas import AnalyzeRequest,AnalyzeResponseV2
from app.signal_engine import analyze_thread_v2
from app.context_signals import analyze_context
from app.context_assessment import assess
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import file_sha
P=R/'reports/ai_update/camping_context_20261103'
REF=json.loads((R/'tests/fixtures/ai_update/camping_reference.json').read_text(encoding='utf-8'))
PAYLOAD=json.loads((R/REF['input_file']).read_text(encoding='utf-8'))
CACHE=json.loads((P/'before_live.json').read_text(encoding='utf-8'))

class Cached:
    threshold=.41
    def __init__(self,port):
        self.name='Actual '+port+' API score cache; not new inference'
        self.scores={c['comment_id']:c['toxicity_score'] for c in CACHE[port]['comments']}
        self.by_text={c['text']:self.scores[c['comment_id']] for c in PAYLOAD['comments']}
    def predict_scores(self,texts):return [self.by_text[t] for t in texts]

@pytest.fixture(scope='module',params=['8020','8021'])
def camping(request):return AnalyzeResponseV2.model_validate(analyze_thread_v2(AnalyzeRequest.model_validate(PAYLOAD),Cached(request.param)))

@pytest.mark.parametrize('cid,label',list(REF['labels'].items()))
def test_all_thirty_reference_labels(camping,cid,label):
    row=next(c for c in camping.comments if c.comment_id==cid)
    assert row.moderation_assessment.label==label
    assert row.moderation_assessment.advisory_only and not row.moderation_assessment.human_gold and not row.policy_risk.executed

def test_all_four_attacks_have_grounded_target_even_below_raw_threshold(camping):
    rows={c.comment_id:c for c in camping.comments}
    chain=next(e for e in camping.evidence if e.actor_user_id=='U04' and e.target_user_id=='U03')
    assert chain.evidence_comment_ids==REF['attack_evidence_ids']
    for cid in REF['attack_evidence_ids']:
        row=rows[cid]
        assert row.directed_at_user_id=='U03' and row.analysis_signals.attack_instance_candidate
        assert row.analysis_signals.attack_instance_basis=='context_with_grounded_target'
    assert rows['c09'].toxicity_score<.41 and not rows['c09'].toxic_for_moderation and not rows['c09'].toxic_for_repeated_rule
    assert rows['c09'].policy_risk.band=='REVIEW'
    assert 'DEFENSE' not in rows['c18'].analysis_signals.context_tags
    for cid in ('c17','c22','c23','c24','c25'):
        assert rows[cid].directed_at_user_id is None and not rows[cid].analysis_signals.attack_instance_candidate

@pytest.mark.parametrize('cid,tag',list(REF['focus_context_AI_reference'].items()))
def test_non_attack_discourse_has_precise_context(cid,tag):
    comment=next(c for c in PAYLOAD['comments'] if c['comment_id']==cid)
    ctx=analyze_context(comment['text'])
    assert tag in ctx.tags and not ctx.attack_candidate
    if cid=='c25':assert 'ACKNOWLEDGEMENT' not in ctx.tags

@pytest.mark.parametrize('text',[
 'Cậu làm việc như hạch rồi còn đổ lỗi.',
 'Ông đúng là gánh đội ngược.',
 'Vụng như mày mà còn đổ cho cả nhóm.',
 'Làm việc thiếu não thì chịu bị chửi thôi.',
 'T nhận lời xin lỗi, nhưng mày làm ăn như hạch.',
 'Xin lỗi, nhưng bạn đúng là gánh team ngược.',
 'Thôi ông ơi. Mày vẫn thiếu não thì chịu bị chửi.'])
def test_new_personal_attack_survives_apology_or_intervention(text):
    for value in (text,unicodedata.normalize('NFD',text)):
        ctx=analyze_context(value)
        assert ctx.attack_candidate and not ctx.non_attack_context_confirmed
        assert assess(ctx,False)[0].label=='TOXIC'

@pytest.mark.parametrize('text',[
 'App này làm ăn như hạch.',
 'Bạn không phải gánh team ngược.',
 'Đừng bảo cậu ấy “gánh team ngược”.',
 'Tôi xin lỗi vì đã gọi bạn làm ăn như hạch.',
 'Không phải cứ làm việc thiếu não thì chịu bị chửi.',
 'Xin lỗi vì đã nói “làm việc thiếu não thì chịu bị chửi thôi”.',
 'Bạn đừng gọi tôi làm ăn như hạch.',
 'Bạn có thể nói về câu “thiếu não” trong bài không?'])
def test_work_criticism_negation_and_quotation_are_not_personal_attacks(text):
    assert not analyze_context(text).attack_candidate

def test_reporting_victim_blaming_in_apology_is_safe_at_high_raw_score():
    ctx=analyze_context('Xin lỗi vì đã nói “làm việc thiếu não thì chịu bị chửi thôi”.')
    assert assess(ctx,True)[0].label=='CLEAN'

def test_without_parent_or_mentions_no_grounded_repeated_target():
    p=copy.deepcopy(PAYLOAD)
    for c in p['comments']:c['parent_id']=None
    out=analyze_thread_v2(AnalyzeRequest.model_validate(p),Cached('8021'))
    assert not out['evidence']

def test_actor_target_and_comment_ids_are_not_hardcoded():
    p=copy.deepcopy(PAYLOAD);p['thread_id']='another_thread'
    ids={c['comment_id']:'item_'+str(i) for i,c in enumerate(p['comments'])}
    users={uid:'person_'+str(i) for i,uid in enumerate(sorted({c['user_id'] for c in p['comments']}))}
    values={}
    original=Cached('8021')
    for c in p['comments']:
        score=original.by_text[c['text']]
        c['comment_id']=ids[c['comment_id']];c['parent_id']=ids.get(c.get('parent_id'));c['user_id']=users[c['user_id']]
        for old,new in users.items():c['text']=re.sub(r'(?<!\w)'+re.escape(old)+r'(?!\w)',new,c['text'])
        values[c['text']]=score
    original.by_text=values
    out=analyze_thread_v2(AnalyzeRequest.model_validate(p),original)
    chain=next(e for e in out['evidence'] if e['actor_user_id']==users['U04'])
    assert chain['target_user_id']==users['U03'] and chain['evidence_comment_ids']==[ids[cid] for cid in REF['attack_evidence_ids']]

def test_reference_and_original_input_are_frozen_and_not_human_gold():
    lock=json.loads((P/'before_lock.json').read_text(encoding='utf-8'))
    assert not REF['human_gold'] and not REF['training_eligible']
    assert file_sha(R/REF['input_file'])==REF['input_sha256']==lock['input_sha256']
    assert file_sha(R/'tests/fixtures/ai_update/camping_reference.json')==lock['reference_sha256']

def test_additive_schema_and_older_v2_response_remain_compatible():
    schema=AnalyzeResponseV2.model_json_schema()
    assert json.loads((R/'contracts/analysis_response_v2.schema.json').read_text(encoding='utf-8'))==schema
    fields=schema['$defs']['AnalysisSignalsOut']
    assert 'attack_instance_basis' not in fields['required']
    old=AnalyzeResponseV2.model_validate(CACHE['8021'])
    assert old.analysis_version=='2.0'
