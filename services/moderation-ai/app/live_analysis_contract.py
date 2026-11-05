"""Additive internal live response, vendored identically by Social/AI services."""
from typing import Literal
from pydantic import AwareDatetime,Field
from .moderation_contract import ContractModel,OpaqueId,ModerationResponse

class GroundedInstance(ContractModel):
    comment_id:OpaqueId
    actor_user_id:OpaqueId
    target_user_id:OpaqueId
    timestamp:AwareDatetime
    context_confidence:Literal['medium','high']
    target_confidence:Literal['medium','high']
    target_method:str=Field(min_length=1,max_length=100)
    target_evidence_ids:list[OpaqueId]=Field(min_length=1,max_length=51)

class CurrentAdvisory(ContractModel):
    reply_to_user_id:OpaqueId|None
    directed_at_user_id:OpaqueId|None
    directed_attack_candidate:bool
    base_attack_instance_candidate:bool
    attack_instance_candidate:bool
    instance_gate_reason:Literal['v5_grounded','reported_predicate_only','insufficient_context_or_target']
    context_tags:list[str]=Field(max_length=20)
    context_cues:list[str]=Field(max_length=50)
    assessment_label:Literal['CLEAN','TOXIC','UNCERTAIN']
    assessment_basis:str=Field(max_length=100)
    policy_risk:Literal['LOW','REVIEW','UNKNOWN']
    policy_executed:Literal[False]=False

class ConversationSignals(ContractModel):
    schema_version:Literal['live-analysis-1.0']='live-analysis-1.0'
    processor:Literal['default-v5','experimental-v6.2']
    instance_gate_version:Literal['live-provenance-v1']='live-provenance-v1'
    rules_version:dict[str,str]=Field(max_length=10)
    model_fingerprint:str=Field(pattern=r'^[0-9a-f]{64}$')
    current:CurrentAdvisory
    attack_instances:list[GroundedInstance]=Field(max_length=51)
    context_complete:bool
    horizon_seconds:int=Field(ge=60,le=86400)
    cached_texts:int=Field(ge=0,le=51)
    neural_texts:int=Field(ge=0,le=51)
    analysis_ms:float=Field(ge=0)

class LiveModerationResponse(ModerationResponse):
    conversation_signals:ConversationSignals
