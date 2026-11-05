"""User references remain separate from gold; constant-score cases test context rules."""
import copy,json,re,sys,unicodedata
from pathlib import Path
import pytest
from app.schemas import AnalyzeRequest,AnalyzeResponseV2
from app.signal_engine import analyze_thread_v2
from app.context_signals import analyze_context
from app.context_assessment import assess
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from synthetic_data.pipeline import file_sha
DATA=ROOT/'datasets/fixtures/context_recovery_v1';REPORT=ROOT/'reports/ai_update/context_recovery_20261103'
REF=json.loads((DATA/'game_rank_30_reference.json').read_text(encoding='utf-8'))
PAYLOAD=json.loads((ROOT/REF['input_file']).read_text(encoding='utf-8'))
CACHE=json.loads((REPORT/'score_cache.json').read_text(encoding='utf-8'))[REF['thread_id']]
class OriginalScoreCache:
    threshold=.41;name='V1 actual CPU cached scores, no optimizer'
    def predict_scores(self,texts):
        lookup=dict(zip([c['text'] for c in PAYLOAD['comments']],CACHE));return [lookup[t] for t in texts]

@pytest.fixture(scope='module')
def game():return AnalyzeResponseV2.model_validate(analyze_thread_v2(AnalyzeRequest.model_validate(PAYLOAD),OriginalScoreCache()))

@pytest.mark.parametrize('cid,label',list(REF['labels'].items()))
def test_all_thirty_user_labels_and_raw_are_separate(game,cid,label):
    row=next(c for c in game.comments if c.comment_id==cid)
    assert row.moderation_assessment.label==label
    assert row.moderation_assessment.advisory_only and not row.moderation_assessment.human_gold and not row.policy_risk.executed
    if cid in ('c12','c16','c21','c23','c24'):
        assert row.toxic_for_moderation and row.toxicity_score>=.41
        assert row.moderation_assessment.label=='CLEAN' and row.policy_risk.band=='REVIEW'

@pytest.mark.parametrize('cid,tag',list(REF['focus_context_AI_reference'].items()))
def test_focus_context_is_explicit_and_not_a_new_attack(game,cid,tag):
    row=next(c for c in game.comments if c.comment_id==cid)
    assert tag in row.analysis_signals.context_tags
    assert not row.analysis_signals.directed_attack_candidate and not row.analysis_signals.attack_instance_candidate
    assert row.directed_at_user_id is None


def test_reply_recipient_is_not_an_attack_target_and_chain_is_exact(game):
    lookup={c.comment_id:c for c in game.comments};assert lookup['c12'].reply_to_user_id=='U02' and lookup['c12'].directed_at_user_id is None
    assert lookup['c21'].reply_to_user_id=='U04' and lookup['c21'].directed_at_user_id is None
    assert lookup['c23'].reply_to_user_id=='U03' and lookup['c23'].directed_at_user_id is None
    chain=next(e for e in game.evidence if e.actor_user_id=='U02' and e.target_user_id=='U03')
    assert chain.evidence_comment_ids==['c08','c11','c15','c18']
    assert all(lookup[cid].directed_at_user_id=='U03' for cid in chain.evidence_comment_ids)

@pytest.mark.parametrize('text',[
 'Xin lỗi nhưng mày vẫn ngu.',
 'Xin lỗi vì đã chửi. Mày là đồ vô dụng.',
 'Mình nhận lỗi vì đã chửi, mày vẫn là đồ ngu.',
 'Mày ngu thật, nhưng đừng chửi nhau.',
 'Xin lỗi chứ mày đạo đức giả phát ngán.',
 'Sorry, you are still garbage.',
 'Xin lỗi vì đã gọi mày ngu và mày vẫn là đồ vô dụng.',
 'Xin lỗi nhưng tao sẽ đánh mày nếu còn hỏi.',
 'Mày đúng là “đồ ngu”, nói thế mới chính xác.'])
def test_apology_or_intervention_does_not_erase_fresh_attack(text):
    context=analyze_context(text);result,_=assess(context,False)
    assert context.attack_candidate and not context.non_attack_context_confirmed and result.label=='TOXIC'

@pytest.mark.parametrize('text',[
 'Tui nhận lỗi vì đã nói bậy.',
 'Lúc đó tôi nóng quá nên nói quá lời.',
 'Cảm ơn vì đã xin lỗi, những lời đó vẫn làm mình tổn thương.',
 'Đừng gọi người khác là “đồ ngu”.',
 'Bàn chiến thuật thì được, xúc phạm người ta thì dừng nhé.',
 'Vế đầu của bạn đang xúc phạm mình đó.'])
def test_bounded_non_attack_context_handles_high_raw_score(text):
    context=analyze_context(text);result,risk=assess(context,True)
    assert not context.attack_candidate and result.label=='CLEAN'
    assert risk.band=='REVIEW' and risk.reason=='raw_context_disagreement'

@pytest.mark.parametrize('text',[
 'Bạn tìm chỗ ngủ trước đi.',
 'Vậy nhớ xét hai cầu thủ phòng ngự cuối.',
 'Bản gốc dùng một thành ngữ khó đó.'])
def test_accents_prevent_false_insult_and_support_decomposed_unicode(text):
    for variant in (text,unicodedata.normalize('NFD',text)):
        assert not analyze_context(variant).attack_candidate


def test_unknown_personal_clause_after_apology_abstains_instead_of_blanket_clean():
    c=analyze_context('Xin lỗi nhưng bạn xứng đáng bị đối xử như vậy.')
    assert assess(c,True)[0].label!='CLEAN'


def test_victim_blaming_is_not_exculpatory_defense():
    c=analyze_context('Làm việc thiếu não thì chịu bị chửi thôi.')
    assert not c.non_attack_context_confirmed and assess(c,True)[0].label=='TOXIC'


def test_rules_do_not_depend_on_fixture_or_user_ids():
    p=copy.deepcopy(PAYLOAD);p['thread_id']='a_different_conversation'
    comments={c['comment_id']:'post_'+str(i) for i,c in enumerate(p['comments'])}
    users={u:'member_'+str(i) for i,u in enumerate(sorted({c['user_id'] for c in p['comments']}))}
    for c in p['comments']:
        c['comment_id']=comments[c['comment_id']];c['parent_id']=comments.get(c.get('parent_id'));c['user_id']=users[c['user_id']]
        for old,new in users.items():c['text']=re.sub(r'(?<!\w)'+re.escape(old)+r'(?!\w)',new,c['text'])
    class High:
        name='deliberate high-score unit stub';threshold=.41
        def predict_scores(self,texts):return [.9]*len(texts)
    result=analyze_thread_v2(AnalyzeRequest.model_validate(p),High())
    chain=next(e for e in result['evidence'] if e['actor_user_id']==users['U02'] and e['target_user_id']==users['U03'])
    assert chain['evidence_comment_ids']==[comments[c] for c in ('c08','c11','c15','c18')]


def test_labels_and_source_fixture_are_frozen_separately_from_human_gold():
    m=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'));lock=json.loads((REPORT/'before_lock.json').read_text(encoding='utf-8'))
    assert not m['human_gold'] and REF['label_source']=='user_provided_reference' and not REF['human_gold']
    assert file_sha(DATA/'manifest.json')==lock['new_dataset_manifest_sha256']
    assert file_sha(DATA/'game_rank_30_reference.json')==m['user_reference_sha256']
    assert file_sha(ROOT/REF['input_file'])==REF['input_sha256']
    assert all(file_sha(DATA/path)==expected for path,expected in m['file_sha256'].items())


def test_new_ai_threads_have_valid_parent_and_repeated_evidence():
    for p in sorted((DATA/'threads').glob('*.json')):
        t=json.loads(p.read_text(encoding='utf-8'));AnalyzeRequest.model_validate(json.loads((DATA/'dashboard_threads'/p.name).read_text(encoding='utf-8')))
        prior={}
        for c in t['comments']:
            a=c['annotation'];pair=(c['user_id'],a['directed_at_user_id'])
            if a['is_repeated_attack']:
                assert len(a['evidence_comment_ids'])>=2
                assert all(cid==c['comment_id'] or cid in prior.get(pair,[]) for cid in a['evidence_comment_ids'])
            if a['label']=='TOXIC' and a['is_directed_attack']:prior.setdefault(pair,[]).append(c['comment_id'])


