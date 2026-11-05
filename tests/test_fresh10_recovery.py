import csv,json
from pathlib import Path
import pytest
from app.schemas import AnalyzeRequest
from app.experiments.fresh10_v6 import analyze_thread_v6
from app.experiments.fresh10_v6 import context_v6
R=Path(__file__).resolve().parents[1];D=R/'datasets/fixtures/fresh10_regression_v1'

def replay(number):
    t=json.loads(next((D/'inputs').glob('TEST'+str(number).zfill(2)+'_*.json')).read_text(encoding='utf-8'))
    out=json.loads(next((D/'analysis').glob('*_'+str(number).zfill(2)+'_*analysis.json')).read_text(encoding='utf-8'))
    scores={c['comment_id']:c['toxicity_score'] for c in out['comments']};mapping={c['text']:scores[c['comment_id']] for c in t['comments']}
    class Cached:
        threshold=.41;name='user_exported_r06_cache'
        def predict_scores(self,texts):return [mapping[text] for text in texts]
    return analyze_thread_v6(AnalyzeRequest.model_validate(t),Cached())

@pytest.mark.parametrize('number,cid,expected',[(9,'c17','TOXIC'),(10,'c14','CLEAN')])
def test_priority_reference_labels_without_changing_raw_score(number,cid,expected):
    out=replay(number);row=next(c for c in out['comments'] if c['comment_id']==cid)
    assert row['moderation_assessment']['label']==expected
    assert row['toxicity_score']==(.798809 if number==9 else .011560)

@pytest.mark.parametrize('number,cid',[(5,'c08'),(5,'c10'),(5,'c13'),(2,'c10')])
def test_frozen_self_defense_intervention_self_mocking_references(number,cid):
    row=next(c for c in replay(number)['comments'] if c['comment_id']==cid)
    assert row['moderation_assessment']['label']=='CLEAN'
    assert not row['analysis_signals']['attack_instance_candidate'] and row['directed_at_user_id'] is None

def test_mutual_pairs_remain_distinct_and_single_attack_actors_do_not_merge():
    out=replay(7);pairs={(e['actor_user_id'],e['target_user_id']):e['evidence_comment_ids'] for e in out['evidence']}
    assert pairs=={('U02','U03'):['c06','c11'],('U03','U02'):['c07','c12']}
    assert not replay(5)['evidence']

@pytest.mark.parametrize('text',[
    'Mình đổi bạn gói hạt ngô đã để khô nhé.',
    'Máy ngu này lại quên mạng WiFi.',
    'T đang cười cái máy tính của chính t thôi.',
    'Đừng gọi bạn ấy là kiểu người thích bắt nạt.',
    'Mình xin lỗi vì đã nói bạn sống kiểu vô ý thức.',
    'Tôi trích dẫn “you are fucking clueless” để báo lại sự việc.',
])
def test_non_personal_or_reported_language_does_not_qualify_as_new_attack(text):
    context,_=context_v6(text,{'A','B'})
    assert not context.attack_candidate

@pytest.mark.parametrize('text',[
    'Mình nhận lời xin lỗi nhưng mày vẫn ngu.',
    'T xin lỗi vì đã gọi b như vậy, nhưng b sống kiểu vô ý thức.',
    'Có hạt ngò rồi, bạn đúng là đồ ngu mới không biết gieo.',
    'Đừng công kích người khác. Nhưng mày đúng là đồ vô dụng.',
])
def test_safe_fragment_does_not_erase_new_attack_elsewhere(text):
    context,_=context_v6(text,{'A','B'})
    assert context.attack_candidate and not context.non_attack_context_confirmed

def test_named_participant_can_share_spelling_with_a_culinary_noun():
    context,_=context_v6('Ngô đúng là đồ ngu khi nói vậy.',{'Ngô','B'})
    assert context.attack_candidate

@pytest.mark.parametrize('text',[
    'T đọc rồi. Cảm ơn vì xin lỗi, nhưng mấy lời đó làm t tụt mood thật.',
    'Bản dịch kia dùng “trở lại” còn bản này dùng “quay về”, nghĩa lệch nhẹ.',
    'Mình không tham gia công kích không có nghĩa phải nhận lời xúc phạm.',
])
def test_regression_safe_clauses_and_non_personal_homographs(text):
    c,_=context_v6(text,{'A','B'})
    assert c.non_attack_context_confirmed and not c.unresolved_new_clause

def test_existing_elliptical_direct_address_cue_is_preserved():
    c,_=context_v6('Đánh ngu thì nhận, đừng đổ lỗi đường truyền.',{'A','B'})
    assert c.attack_candidate

def test_default_v5_stays_unchanged_after_opt_in_research_call():
    from app.context_signals import analyze_context
    text='Quá tuyệt, t đổi bạn ít hạt ngò nha.'
    before=analyze_context(text).model_dump()
    assert not context_v6(text)[0].attack_candidate
    assert analyze_context(text).model_dump()==before and before['version']=='context-v5'

@pytest.mark.parametrize('text',[
    'Tôi xin lỗi vì đã gọi bạn là thiên tài tự phong hôm qua.',
    'Tôi nhận lỗi vì đã gọi bạn là “đồ ngu” trong buổi họp.',
    'Mình trích dẫn bạn là “kẻ vô dụng” để lưu bằng chứng.',
])
def test_reported_address_assignment_does_not_override_reporting_scope(text):
    assert not context_v6(text,{'A','B'})[0].attack_candidate

@pytest.mark.parametrize('text',[
    'Mày là “đồ ngu”, nói vậy hiểu chưa?',
    'Tao đã gọi mày ngu là đúng, mày xứng đáng.',
])
def test_actual_assignment_and_endorsed_abuse_are_still_attacks(text):
    assert context_v6(text,{'A','B'})[0].attack_candidate
