"""Synthetic-reference development cases; no labels promoted to human gold."""
import json,unicodedata
from datetime import datetime,timezone
from pathlib import Path
import pytest
from app.context_signals import analyze_context
from app.context_assessment import assess
from app.target_signals import infer_target
from app.schemas import CommentIn
R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('thread,cid',[
 ('SGZ500_0205','SGZ500_0205_C07'),('SGZ500_0218','SGZ500_0218_C06'),('SGZ500_0339','SGZ500_0339_C02')])
def test_frozen_existing_indirect_references(thread,cid):
    t=json.loads((R/'datasets/synthetic_conversations/genz_v2/threads'/(thread+'.json')).read_text(encoding='utf-8'))
    comment=next(c for c in t['comments'] if c['comment_id']==cid)
    assert comment['annotation']['label']=='TOXIC' and comment['annotation']['label_source']=='synthetic'
    for text in (comment['text'],unicodedata.normalize('NFD',comment['text'])):
        ctx=analyze_context(text)
        assert ctx.attack_candidate and assess(ctx,False)[0].label=='TOXIC'
        assert ctx.attack_clause_spans

@pytest.mark.parametrize('text',[
 'Đầu ông chỉ đủ để đội mũ thôi.',
 'Chắc đầu óc cậu chỉ tới mức đó.',
 'Người nghe phải có lòng thương lớn mới nghe hết giọng mày.',
 'Xin lỗi, nhưng đầu mày chắc chỉ đủ để đội cái nón thôi.',
 'T nhận lời xin lỗi, nhưng chắc đầu óc mày chỉ đến mức này.'])
def test_indirect_personal_disparagement_still_attack_after_apology(text):
    assert analyze_context(text).attack_candidate

@pytest.mark.parametrize('text',[
 'Cái đầu ma nơ canh này chỉ để đội nón trưng bày.',
 'Mũ bảo hiểm của bạn chỉ đủ để đội khi chạy xe đạp.',
 'Người nghe cần kiên nhẫn mới nghe hết bài giải dài của bạn.',
 'Đừng nói “đầu mày chỉ đủ để đội cái nón”.',
 'Xin lỗi vì đã nói “chắc đầu óc mày chỉ đến mức này”.',
 'Bạn không phải đồ ngu.'])
def test_literal_work_criticism_quotes_and_negation_are_not_attacks(text):
    assert not analyze_context(text).attack_candidate

@pytest.mark.parametrize('text',[
 'Câu này hơi toxic rồi nha, mình đang cân nhắc mua mà rén.',
 'Mình tiếp thu góp ý chuyên môn, nhưng so sánh xúc phạm thì không.'])
def test_intervention_and_boundary_handle_high_raw_without_hiding_new_attack(text):
    ctx=analyze_context(text)
    assert assess(ctx,True)[0].label=='CLEAN'
    assert assess(analyze_context(text+' Nhưng mày là đồ ngu.'),False)[0].label=='TOXIC'

def comment(cid,user,text,parent=None):
    return CommentIn(comment_id=cid,user_id=user,text=text,parent_id=parent,timestamp=datetime.now(timezone.utc))

def test_only_names_in_actual_attack_clause_are_targets():
    rows=[comment('root','alice','Mình đăng bài'),comment('other','bob','Trao đổi thôi'),comment('third','carol','Mình đang xem')]
    c=comment('reply','actor','alice và bob đang trao đổi; nhưng carol là đồ ngu.','other')
    # Named participants are input metadata; expected target remains unchanged.
    out=infer_target(c,{r.comment_id:r for r in rows+[c]},analyze_context(c.text,[r.user_id for r in rows]))
    assert out.candidate=='carol' and out.confidence=='high'

def test_background_name_does_not_override_actual_direct_reply():
    a=comment('root','alice','Mình đăng bài');b=comment('other','bob','Ý mình khác')
    c=comment('reply','actor','alice nói về kế hoạch; nhưng mày là đồ ngu.','other')
    out=infer_target(c,{r.comment_id:r for r in [a,b,c]},analyze_context(c.text))
    assert out.candidate=='bob' and out.confidence=='medium'

def test_bare_root_attack_has_no_invented_addressee_from_future_participants():
    a=comment('root','actor','Mày nói ngu thế thì làm clip dạy ai?')
    b=comment('later','victim','Bạn góp ý nội dung giúp mình.','root')
    assert infer_target(a,{r.comment_id:r for r in [a,b]},analyze_context(a.text)).candidate is None

def test_existing_shipping_reference_has_two_grounded_attacks_not_just_raw_scores():
    from app.schemas import AnalyzeRequest
    from app.signal_engine import analyze_thread_v2
    tid='SGZ500_0205'
    p=json.loads((R/'datasets/synthetic_conversations/genz_v2/dashboard_threads'/(tid+'.json')).read_text(encoding='utf-8'))
    scores=json.loads((R/'reports/ai_update/context_recovery_20261103/score_cache.json').read_text(encoding='utf-8'))[tid]
    lookup={c['text']:score for c,score in zip(p['comments'],scores)}
    class Cached:
        threshold=.41;name='Existing actual V1 score cache, no new inference'
        def predict_scores(self,texts):return [lookup[text] for text in texts]
    out=analyze_thread_v2(AnalyzeRequest.model_validate(p),Cached())
    chain=next(e for e in out['evidence'] if e['actor_user_id']==tid+'_U02' and e['target_user_id']==tid+'_U01')
    assert chain['evidence_comment_ids']==[tid+'_C03',tid+'_C07']
    assert not analyze_context('Đừng gọi người khác là “loại khách hãm”.').attack_candidate
