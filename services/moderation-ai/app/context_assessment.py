"""Separate advisory assessment; never rewrites raw scores or executes visibility policy."""
from typing import Literal
from pydantic import BaseModel
VERSION='context-assessment-v1'
class ModerationAssessment(BaseModel):
    label:Literal['CLEAN','TOXIC','UNCERTAIN']
    basis:Literal['new_directed_attack','bounded_non_attack_context','unresolved_new_clause','raw_model_fallback']
    version:str=VERSION
    human_gold:Literal[False]=False
    advisory_only:Literal[True]=True
class PolicyRiskSignal(BaseModel):
    band:Literal['LOW','REVIEW','UNKNOWN']
    reason:Literal['attack_review','raw_context_disagreement','uncertain_context','raw_model_review','no_review_trigger']
    executed:Literal[False]=False

def assess(context,raw_toxic:bool):
    if context.attack_candidate:label='TOXIC';basis='new_directed_attack'
    elif context.unresolved_new_clause:label='UNCERTAIN';basis='unresolved_new_clause'
    elif context.non_attack_context_confirmed:label='CLEAN';basis='bounded_non_attack_context'
    else:label='TOXIC' if raw_toxic else 'CLEAN';basis='raw_model_fallback'
    result=ModerationAssessment(label=label,basis=basis)
    reason='attack_review' if context.attack_candidate else 'uncertain_context' if label=='UNCERTAIN' else 'raw_context_disagreement' if raw_toxic and label=='CLEAN' else 'raw_model_review' if raw_toxic else 'no_review_trigger'
    risk=PolicyRiskSignal(band='REVIEW' if reason!='no_review_trigger' else 'LOW',reason=reason)
    return result,risk
