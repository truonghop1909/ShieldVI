"""Supplemental red probes for a newly observed challenge bug, not a rule fix.

Run explicitly with pytest against this file. Correct expectations remain red;
standard root suite and these failing diagnostic probes are reported separately.
"""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'services/moderation-ai'))
from app.experiments.fresh10_v6 import context_v6
P=Path(__file__).resolve().parent

def test_narrative_quote_assignment_is_not_a_fresh_attack():
    text='Tác giả viết câu “mày đúng là đồ ngu” để cho thấy cách quản đốc đối xử với thợ.'
    context,trace=context_v6(text,{'N01','N02','N03'})
    assert not context.attack_candidate,trace

def test_quoted_character_does_not_create_target_for_the_comment_author():
    outputs=json.loads((P/'new_challenge/after.json').read_text())
    thread=next(x['output'] for x in outputs if x['output']['thread_id']=='NOV10_AUDIT_CHALLENGE_02')
    row=next(c for c in thread['comments'] if c['comment_id']=='c02')
    assert not row['analysis_signals']['attack_instance_candidate'] and row['directed_at_user_id'] is None

def test_direct_assignment_outside_quote_must_still_be_recognized():
    assert context_v6('Mày đúng là “đồ ngu”.',{'A','B'})[0].attack_candidate
