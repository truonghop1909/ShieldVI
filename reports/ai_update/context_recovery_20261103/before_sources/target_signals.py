"""Attack-target candidates, distinct from legacy reply-recipient heuristics."""
import re
from typing import Literal
from pydantic import BaseModel,Field
from .context_signals import ContextSignals,DIRECT
from .lexical import QUOTED,fold
VERSION='target-v3'
class TargetSignals(BaseModel):
    version:str=VERSION
    candidate:str|None=None
    method:str='abstain'
    confidence:Literal['none','low','medium','high']='none'
    evidence_comment_ids:list[str]=Field(default_factory=list)
    needs_human_review:bool=True

def infer_target(comment,by_id:dict,context:ContextSignals,past_targets=(),past_evidence_ids=())->TargetSignals:
    if not context.attack_candidate:return TargetSignals(method='non_attack_or_uncertain')
    actor=comment.user_id
    text=QUOTED.sub(' ',comment.text)
    participants={c.user_id for c in by_id.values()}-{actor}
    textual=[uid for uid in sorted(participants) if re.search(r'(?<!\w)@?'+re.escape(uid)+r'(?!\w)',text,re.I)]
    platform=list(dict.fromkeys(uid for uid in comment.mentioned_user_ids if uid!=actor))
    mentioned=set(textual)|set(platform)
    if len(mentioned)>1:return TargetSignals(method='ambiguous_mentions')
    if len(mentioned)==1:
        uid=next(iter(mentioned))
        return TargetSignals(candidate=uid,method='mapped_text_reference' if uid in textual else 'platform_mention',confidence='high',evidence_comment_ids=[comment.comment_id])
    parent=by_id.get(comment.parent_id)
    if parent and parent.user_id!=actor:
        history=set(past_targets)
        if history and history!={parent.user_id}:return TargetSignals(method='history_reply_conflict',evidence_comment_ids=[parent.comment_id])
        addressed=bool(re.search(r'\b(?:may|m|ban|you|cau|ong|ba)\b',fold(text)))
        continued=bool(history=={parent.user_id} and past_evidence_ids)
        return TargetSignals(candidate=parent.user_id,method='addressed_reply' if addressed else 'continued_addressed_reply' if continued else 'parent_candidate',confidence='medium' if addressed or continued else 'low',evidence_comment_ids=list(dict.fromkeys([comment.comment_id,parent.comment_id]+list(past_evidence_ids[-2:]))))
    if len(set(past_targets))==1 and past_targets:
        return TargetSignals(candidate=past_targets[-1],method='history_candidate',confidence='low',evidence_comment_ids=[comment.comment_id])
    return TargetSignals(method='no_grounded_addressee')
