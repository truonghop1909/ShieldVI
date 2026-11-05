"""Attack-target candidates, distinct from legacy reply-recipient heuristics."""
import re
from typing import Literal
from pydantic import BaseModel,Field
from .context_signals import ContextSignals,DIRECT,context_view
from .lexical import QUOTED,fold
VERSION='target-v5'
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
    view=context_view(comment.text)
    text=' '.join(QUOTED.sub(' ',view[a:b]) for a,b in context.attack_clause_spans) if context.attack_clause_spans else QUOTED.sub(' ',view)
    participants={c.user_id for c in by_id.values()}-{actor}
    textual=[uid for uid in sorted(participants) if re.search(r'(?<!\w)@?'+re.escape(context_view(uid))+r'(?!\w)',text,re.I)]
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

def resolve_root_exchange(comment,by_id,context,grounded_instances,contexts)->TargetSignals:
    """Retrospective candidate only with a reciprocal self-response and later anchor.

    Neither a lone reply nor a root-author fallback identifies an attack target.
    The bounded exchange is available only when reanalyzing the whole thread.
    """
    if comment.parent_id or not context.attack_candidate or not DIRECT.search(context_view(comment.text)):
        return TargetSignals(method='no_reciprocal_exchange')
    ordered=sorted(by_id.values(),key=lambda c:(c.timestamp,c.comment_id));positions={c.comment_id:i for i,c in enumerate(ordered)}
    anchors=[(c,t) for c,t in grounded_instances if c.user_id==comment.user_id and
        0<(c.timestamp-comment.timestamp).total_seconds()<=1800 and
        0<positions[c.comment_id]-positions[comment.comment_id]<=16]
    candidates={t.candidate for _,t in anchors}
    if len(candidates)!=1:return TargetSignals(method='ambiguous_or_missing_later_anchor')
    target=next(iter(candidates));anchor=anchors[0][0]
    responses=[]
    for reply in ordered:
        if reply.parent_id!=comment.comment_id or reply.user_id!=target or not comment.timestamp<reply.timestamp<anchor.timestamp:continue
        rc=contexts[reply.comment_id];s=context_view(reply.text)
        self_response=bool(re.search(r'\b(?:minh|toi|tui|to) (?:se |da |dang |van )?(?:kiem (?:lai|tra)|sua|dinh chinh|bo sung)\b',s))
        self_defense=bool(set(rc.tags)&{'DEFENSE','SET_BOUNDARY'}) and bool(re.search(r'\b(?:minh|toi|tui|to)\b',s))
        if not rc.attack_candidate and 'INTERVENTION' not in rc.tags and 'QUOTE' not in rc.tags and (self_response or self_defense):responses.append(reply)
    if not responses:return TargetSignals(method='no_reciprocal_self_response')
    return TargetSignals(candidate=target,method='reciprocal_exchange',confidence='medium',
        evidence_comment_ids=[comment.comment_id,responses[0].comment_id,anchor.comment_id])
