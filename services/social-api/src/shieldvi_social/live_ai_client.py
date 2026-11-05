"""Bounded live HTTP client with independent supplied-snapshot evidence checks."""
import re
import httpx
from pydantic import ValidationError
from .ai_client import AIClient,AIError
from .live_analysis_contract import LiveModerationResponse

def validate_live(payload,result):
    if (result.request_id,result.content_id,result.content_revision)!=(payload.request_id,payload.content_id,payload.content_revision):
        raise AIError('AI_CORRELATION_MISMATCH',True)
    sig=result.conversation_signals
    if sig.processor!='default-v5' or sig.rules_version.get('context')!='context-v5':raise AIError('AI_UNAPPROVED_PROCESSOR',False)
    if sig.horizon_seconds>1800:raise AIError('AI_UNAPPROVED_HORIZON',False)
    lookup={c.comment_id:c for c in payload.context.recent_comments};lookup[payload.content_id]=payload
    users={c.user_id for c in lookup.values()};instances={};basic=set()
    for item in sig.attack_instances:
        row=lookup.get(item.comment_id)
        if row is None or item.comment_id in instances or row.user_id!=item.actor_user_id or item.target_user_id==item.actor_user_id or item.target_user_id not in users:
            raise AIError('AI_INVALID_INSTANCE',True)
        if row.timestamp!=item.timestamp or not 0<=(payload.timestamp-item.timestamp).total_seconds()<=sig.horizon_seconds:
            raise AIError('AI_INVALID_INSTANCE_TIME',True)
        if any(cid not in lookup for cid in item.target_evidence_ids):raise AIError('AI_INVALID_TARGET_CONTEXT',True)
        parent=lookup.get(row.parent_id)
        explicit=item.target_user_id in row.mentioned_user_ids or bool(re.search(r'(?<!\w)@?'+re.escape(item.target_user_id)+r'(?!\w)',row.text,re.I))
        if explicit or (parent and parent.user_id==item.target_user_id):basic.add(item.comment_id)
        instances[item.comment_id]=item
    for cid,item in instances.items():
        if cid in basic:continue
        inverse=[other for key,other in instances.items() if key in basic and other.actor_user_id==item.target_user_id and other.target_user_id==item.actor_user_id]
        if item.target_method!='reciprocal_exchange' or not inverse:raise AIError('AI_UNGROUNDED_TARGET',True)
    current=sig.current;instance=instances.get(payload.content_id)
    if current.attack_instance_candidate:
        if not instance or not current.directed_attack_candidate or current.directed_at_user_id!=instance.target_user_id or current.assessment_label!='TOXIC':
            raise AIError('AI_INVALID_CURRENT_INSTANCE',True)
    elif instance or current.directed_at_user_id is not None:raise AIError('AI_INVALID_CURRENT_INSTANCE',True)
    for item in result.evidence:
        ids=item.evidence_comment_ids
        if item.actor_user_id!=payload.user_id or payload.content_id not in ids or len(set(ids))!=len(ids):raise AIError('AI_INVALID_EVIDENCE',True)
        if any(cid not in instances or instances[cid].actor_user_id!=item.actor_user_id or instances[cid].target_user_id!=item.target_user_id for cid in ids):
            raise AIError('AI_INVALID_EVIDENCE',True)
        if len({instances[cid].timestamp for cid in ids})!=item.n_distinct_timestamps:raise AIError('AI_INVALID_EVIDENCE',True)
    return result

class LiveAIClient(AIClient):
    def moderate(self,payload):
        try:
            with self.client.stream('POST','/api/live/moderate/comment',json=payload.model_dump(mode='json')) as response:
                if response.status_code!=200:
                    hint=response.headers.get('Retry-After','');delay=min(int(hint),3600) if hint.isdigit() and len(hint)<=6 else 0
                    raise AIError(f'AI_HTTP_{response.status_code}',response.status_code==429 or response.status_code>=500,delay)
                body=bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body)>1048576:raise AIError('AI_RESPONSE_TOO_LARGE',True)
                try:result=LiveModerationResponse.model_validate_json(bytes(body))
                except (ValidationError,ValueError):raise AIError('AI_INVALID_SCHEMA',True) from None
        except httpx.TimeoutException:raise AIError('AI_TIMEOUT',True) from None
        except httpx.HTTPError:raise AIError('AI_NETWORK_ERROR',True) from None
        return validate_live(payload,result)
