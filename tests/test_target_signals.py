from datetime import datetime,timezone
from pathlib import Path
import json
from app.schemas import CommentIn
from app.context_signals import analyze_context
from app.target_signals import infer_target

def row(id,user,text,parent=None,mentions=()):
    return CommentIn(comment_id=id,user_id=user,text=text,parent_id=parent,timestamp=datetime.now(timezone.utc),mentioned_user_ids=list(mentions))
def test_text_reference_beats_unrelated_parent_without_legacy_mutation():
    a=row('a','U03','bài của mình');b=row('b','U02','can ngăn');c=row('c','U04','Bạn U03 đúng là đồ ngu.','b')
    out=infer_target(c,{x.comment_id:x for x in [a,b,c]},analyze_context(c.text))
    assert out.candidate=='U03' and out.confidence=='high' and c.parent_id=='b'
def test_multiple_mentions_abstain():
    a=row('a','A','chào');b=row('b','B','chào');c=row('c','C','Mày ngu thật.',mentions=['A','B'])
    assert infer_target(c,{x.comment_id:x for x in [a,b,c]},analyze_context(c.text)).candidate is None

def test_no_root_fallback_or_self_target():
    a=row('a','A','chào');c=row('c','B','Mày ngu thật.')
    assert infer_target(c,{'a':a,'c':c},analyze_context(c.text)).candidate is None
    c.parent_id='c';assert infer_target(c,{'a':a,'c':c},analyze_context(c.text)).candidate is None

def test_quoted_third_party_not_target():
    a=row('a','A','chào');c=row('c','B','Mình trích dẫn “A là đồ ngu” để phản đối.','a')
    assert infer_target(c,{'a':a,'c':c},analyze_context(c.text)).candidate is None

def test_parent_only_candidate_remains_low():
    a=row('a','A','chào');c=row('c','B','Nhảy như NPC bị lag.','a')
    out=infer_target(c,{'a':a,'c':c},analyze_context(c.text))
    assert out.confidence=='low' and out.method=='parent_candidate'

def test_history_conflict_abstains():
    a=row('a','A','chào');c=row('c','B','Mày ngu thật.','a')
    assert infer_target(c,{'a':a,'c':c},analyze_context(c.text),['C','C']).candidate is None

def test_developer_dance_case_has_grounded_U03_reference():
    root=Path(__file__).resolve().parents[1]
    t=json.loads(next((root/'datasets/fixtures/genz_regression').glob('*DANCE*.json')).read_text(encoding='utf-8'))
    rows=[CommentIn.model_validate(c) for c in t['comments']];by_id={c.comment_id:c for c in rows};c=by_id['c15']
    out=infer_target(c,by_id,analyze_context(c.text))
    assert out.candidate=='U03' and out.method=='mapped_text_reference'
