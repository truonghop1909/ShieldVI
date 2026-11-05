import json,unicodedata
from pathlib import Path
import pytest
from app.schemas import AnalyzeRequest
from app.experiments.research_v62 import context_v62,analyze_thread_v62
R=Path(__file__).resolve().parents[1]
QUOTE='Tác giả viết câu “mày đúng là đồ ngu” để cho thấy cách quản đốc đối xử với thợ.'

def test_original_narrative_quote_red_expectation():
    assert not context_v62(QUOTE,{'N01','N02','N03'})[0].attack_candidate

def test_original_quote_target_red_expectation_replays_current_processor():
    # The old red probe read historical v6.1 output; preserve that evidence and
    # replay the SAME input/reference here rather than rewriting the old JSON.
    d=R/'datasets/fixtures/nov10_audit_challenge_v1/threads/NOV10_AUDIT_CHALLENGE_02.json'
    thread=json.loads(d.read_text());payload=AnalyzeRequest.model_validate(thread)
    old=json.loads((R/'reports/ai_update/nov10_audit_20261104/new_challenge/after.json').read_text())
    output=next(x['output'] for x in old if x['output']['thread_id']==thread['thread_id'])
    scores={c['comment_id']:c['toxicity_score'] for c in output['comments']}
    mapping={c['text']:scores[c['comment_id']] for c in thread['comments']}
    class Cache:
        threshold=.41;name='historical_actual_r06_scores'
        def predict_scores(self,texts):return [mapping[t] for t in texts]
    row=analyze_thread_v62(payload,Cache())['comments'][1]
    assert not row['analysis_signals']['attack_instance_candidate'] and row['directed_at_user_id'] is None
    assert row['toxicity_score']==scores['c02']

@pytest.mark.parametrize('text',[
    'Mày đúng là “đồ ngu”.',
    'Cậu là “đồ vô dụng”.',
    'Tôi gọi bạn là “đồ ngu”.',
    'Tôi trích câu “đồ ngu”. Nhưng mày vô dụng thật.',
    'Tôi xin lỗi vì đã chửi, nhưng mày vẫn là đồ ngu.',
    'Họ gọi bạn là “đồ ngu”, nói thế là đúng.',
])
def test_real_attacks_outside_quote_or_endorsed_assignment_are_preserved(text):
    assert context_v62(text,{'A','B','C'})[0].attack_candidate

@pytest.mark.parametrize('text',[
    'Nhân vật nói “bạn là đồ ngu” trong truyện, mình chỉ trích nguyên văn.',
    'Bạn không phải là “đồ ngu”, đừng để lời đó làm bạn buồn.',
    'Đừng gọi cậu ấy là “đồ vô dụng”, nói về lỗi thao tác thôi.',
    'Tôi xin lỗi vì đã gọi bạn là “đồ ngu”.',
    'Câu này chứa từ “ngu”, mình đang kiểm tra chính tả.',
])
def test_reported_negated_or_intervened_quote_is_not_new_attack(text):
    assert not context_v62(text,{'A','B','C'})[0].attack_candidate

def test_quote_spans_are_normalized_coordinates_for_nfd_input():
    ctx,trace=context_v62(unicodedata.normalize('NFD',QUOTE),{'A','B'})
    assert not ctx.attack_candidate
    for item in trace['matches']:
        start,end=item['normalized_span']
        assert trace[item.get('coordinate_view','normalized_view')][start:end]==item['normalized_match']

def test_indirect_content_and_addressee_views_have_explicit_span_coordinates():
    ctx,trace=context_v62(unicodedata.normalize('NFD','Mày chỉ là máy lặp lại, không có suy nghĩ riêng.'),{'A','B'})
    assert ctx.attack_candidate
    for item in trace['matches']:
        start,end=item['normalized_span']
        assert trace[item.get('coordinate_view','normalized_view')][start:end]==item['normalized_match']

def test_cau_noun_and_cau_addressee_are_distinguished():
    assert not context_v62('Tác giả viết câu “mày đúng là đồ ngu”.',{'A','B'})[0].attack_candidate
    assert context_v62('Cậu đúng là đồ ngu.',{'A','B'})[0].attack_candidate

@pytest.mark.parametrize('text',[
    'Ê shop, câu này hơi toxic rồi nha. T đang cân nhắc mua mà rén ngang',
    'Câu sau vẫn là xúc phạm, mình không chấp nhận.',
])
def test_noun_cau_keeps_intervention_and_defense_meaning(text):
    assert context_v62(text,{'A','B'})[0].non_attack_context_confirmed

def test_v61_remains_unchanged_and_keeps_its_known_red_behavior():
    from app.experiments.fresh10_v6 import context_v6
    before=context_v6(QUOTE,{'A','B'})[0].model_dump()
    context_v62(QUOTE,{'A','B'})
    assert context_v6(QUOTE,{'A','B'})[0].model_dump()==before
    assert before['attack_candidate']

@pytest.mark.parametrize('text',[
    '@B cứ hứa mãi mà tự làm chẳng ra gì.',
    '@B vẫn là loại người chỉ biết đổ lỗi rồi hưởng lợi.',
    'Với cái đầu rỗng của mày thì mày định dạy ai?',
    'You are fkn brainless.',
    'Mày chỉ là máy lặp lại, không có suy nghĩ riêng.',
    'b ngồi im cho đỡ phí không khí của nhóm.',
    'Tôi xin lỗi vì lời vừa rồi, nhưng you are a pathetic loser.',
    'Tôi trích “b là pathetic loser”, nhưng mày ngồi im cho đỡ phí oxy.',
])
def test_bounded_indirect_personal_attack_positive_controls(text):
    ctx,_=context_v62(text,{'A','B','C'})
    assert ctx.attack_candidate and not ctx.non_attack_context_confirmed

@pytest.mark.parametrize('text',[
    'Bạn chỉ ra lỗi của đoạn mã nên mình sẽ sửa lại hàm đọc file.',
    'Bạn không phải là loại người chỉ biết đổ lỗi.',
    'Đừng gọi bạn ấy là loại người chỉ biết đổ lỗi.',
    'Tôi xin lỗi vì đã nói bạn tự làm chẳng ra gì.',
    'Mình tự làm chẳng ra gì nên đang học thêm.',
    'Bản dịch bạn tự làm chẳng ra gì, nên mình muốn góp ý cách dùng từ.',
    'Nhân vật mắng “you are brainless” trong truyện.',
    'Bạn giống máy ghi âm, nhớ được rất nhiều lời thoại.',
    'Trình bạn hiện tại có thể cần thêm thời gian để lên mục tiêu đó?',
    'U03 trưng benchmark để giải thích vì sao chọn màn hình.',
    'Bạn dùng thư viện brainless để sinh dữ liệu.',
    'Bạn ngồi im để mình đo hô hấp.',
    'Mình đang tự trêu mình là loại người chỉ biết đổ lỗi, đừng lo.',
    'Tôi thuật lại “mày chỉ là máy copy không có suy nghĩ riêng”, rồi nhắc bạn dừng xúc phạm.',
])
def test_indirect_controls_do_not_confirm_attack_from_criticism_self_report_or_profane_context(text):
    assert not context_v62(text,{'A','B','C','U03'})[0].attack_candidate

def test_exploratory_sarcasm_alone_is_not_an_attack_override():
    ctx,trace=context_v62('Trình bạn hiện tại mà đòi thi cấp đó ư? ambitious thật.',{'A','B'})
    assert trace['exploratory_only'] and not ctx.attack_candidate

def test_new_instances_require_grounded_targets_and_never_merge_distinct_actors():
    payload=AnalyzeRequest.model_validate({'thread_id':'indirect_control','comments':[
        {'comment_id':'a','user_id':'A','timestamp':'2026-11-04T01:00:00Z','text':'Mình gửi danh sách đầu việc để nhóm phân công.'},
        {'comment_id':'b','parent_id':'a','user_id':'B','timestamp':'2026-11-04T01:02:00Z','text':'@A là kiểu người chỉ biết đổ lỗi rồi hưởng lợi.'},
        {'comment_id':'c','parent_id':'a','user_id':'C','timestamp':'2026-11-04T01:04:00Z','text':'@A đúng là đồ ngu.'},
        {'comment_id':'d','parent_id':'a','user_id':'B','timestamp':'2026-11-04T01:06:00Z','text':'Tôi xin lỗi vì đã nói bạn là kiểu người chỉ biết đổ lỗi.'},
        {'comment_id':'e','parent_id':'a','user_id':'B','timestamp':'2026-11-04T01:08:00Z','text':'@A cứ hứa mãi mà tự làm chẳng ra gì.'}]})
    class LowRaw:
        threshold=.41;name='fake_raw_diagnostic_not_classifier_metrics'
        def predict_scores(self,texts):return [.01]*len(texts)
    out=analyze_thread_v62(payload,LowRaw());rows={c['comment_id']:c for c in out['comments']}
    assert out['research_only'] is True
    assert [(e['actor_user_id'],e['target_user_id'],e['evidence_comment_ids']) for e in out['evidence']]==[('B','A',['b','e'])]
    assert not rows['d']['analysis_signals']['attack_instance_candidate']
    assert all(c['toxicity_score']==.01 for c in out['comments'])
