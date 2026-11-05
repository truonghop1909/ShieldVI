import json
from pathlib import Path
import pytest
from app.context_signals import analyze_context,ContextSignals
from app.engine import analyze_thread
from app.schemas import AnalyzeRequest
ROOT=Path(__file__).resolve().parents[1]
CASES=json.loads((ROOT/'tests/fixtures/ai_update/counterexamples.json').read_text(encoding='utf-8'))['cases']
@pytest.mark.parametrize('case',CASES,ids=lambda c:c['case_id'])
def test_context_counterexamples(case):
    result=analyze_context(case['text'])
    assert set(case['expected_context'])<=set(result.tags)
    assert result.attack_candidate==case['expected_attack']
    assert ContextSignals.model_validate(result.model_dump())==result

def test_raw_model_predictions_unchanged():
    class Model:
        name='STUB';threshold=0.41
        def predict_scores(self,texts):return [.9]*len(texts)
    text='Mình xin lỗi vì đã gọi bạn ngu. Mình sai rồi.'
    context=analyze_context(text)
    assert not context.attack_candidate
    request=AnalyzeRequest(thread_id='renamed',comments=[{'comment_id':'different','user_id':'A','timestamp':'2026-01-01T00:00:00Z','text':text}])
    result=analyze_thread(request,Model())
    assert result.comments[0].toxicity_score==.9 and result.comments[0].toxic_for_moderation

def test_does_not_log_raw_text_in_cues():
    result=analyze_context('Xin lỗi vì đã gọi bạn ngu.')
    assert all(' ' not in code for code in result.cues)

@pytest.mark.parametrize('stem,ids',[
 ('GAME', ['c12','c16','c23','c24']),('CAMPING',['c17','c23','c24']),('DANCE',['c23']),('SHOP',['c23']),('FANART',['c24'])])
def test_developer_reference_recovery_cases_are_not_new_attacks(stem,ids):
    path=next(p for p in (ROOT/'datasets/fixtures/genz_regression').glob('*.json') if stem in p.name)
    thread=json.loads(path.read_text(encoding='utf-8'))
    for comment in thread['comments']:
        if comment['comment_id'] in ids:
            signal=analyze_context(comment['text'])
            assert signal.tags
            assert not signal.attack_candidate

def test_recalling_insult_to_child_does_not_treat_con_as_contrast():
    result=analyze_context('Xin lỗi vì đã gọi con ngu.')
    assert 'APOLOGY' in result.tags and not result.attack_candidate

def test_reporting_abuse_does_not_become_a_new_attack():
    result=analyze_context('Bạn đã chửi mình hai lần rồi, mình không muốn nói tiếp.')
    assert 'DEFENSE' in result.tags and not result.attack_candidate

def test_distinguishing_criticism_of_work_and_person_is_intervention():
    result=analyze_context('Chê món ăn khác với chê con người, nên góp ý cụ thể nhé.')
    assert 'INTERVENTION' in result.tags and not result.attack_candidate

@pytest.mark.parametrize('text',[
 'Bạn giúp mình tạo NPC cho game nhé.',
 'Bạn giải thích nghĩa từ cringe af được không?'])
def test_neutral_slang_discussion_is_not_directed_attack(text):
    assert not analyze_context(text).attack_candidate
