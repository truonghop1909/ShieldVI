"""Versioned analysis pipeline; legacy engine remains available for API 0.3 consumers."""
from collections import defaultdict
import hashlib
from .lexical import DATA_DIR
LEXICON_VERSION=hashlib.sha256((DATA_DIR/"active.json").read_bytes()).hexdigest()
from datetime import timezone
from .engine import analyze_thread
from .context_signals import analyze_context,VERSION as CONTEXT_VERSION
from .target_signals import infer_target,resolve_root_exchange,VERSION as TARGET_VERSION
from .context_assessment import assess,VERSION as ASSESSMENT_VERSION
RULE_VERSION='repeated-v5'
ANALYSIS_VERSION='2.0'

def analyze_thread_v2(payload,predictor):
    legacy=analyze_thread(payload,predictor)
    data=legacy.model_dump(mode='json')
    by_id={c.comment_id:c for c in payload.comments}
    history=defaultdict(list);history_ids=defaultdict(list);pairs=defaultdict(list)
    contexts={};targets={};grounded_instances=[]
    for row in data['comments']:
        comment=by_id[row['comment_id']]
        context=analyze_context(comment.text,{c.user_id for c in by_id.values()}-{comment.user_id})
        target=infer_target(comment,by_id,context,history[comment.user_id],history_ids[comment.user_id])
        contexts[comment.comment_id]=context;targets[comment.comment_id]=target
        grounded=target.candidate is not None and target.confidence in ('medium','high')
        # Context evidence is advisory and independent of the frozen raw threshold.
        qualified=bool(context.attack_candidate and context.confidence in ('medium','high') and grounded)
        parent=by_id.get(comment.parent_id)
        row['reply_to_user_id']=parent.user_id if parent else None
        row['directed_at_user_id']=target.candidate if context.attack_candidate and grounded else None
        assessment,risk=assess(context,row['toxic_for_moderation'])
        row['moderation_assessment']=assessment.model_dump()
        row['policy_risk']=risk.model_dump()
        row['analysis_signals']={'context_tags':context.tags,'context':context.model_dump(),
          'directed_attack_candidate':context.attack_candidate,'attack_confidence':context.confidence,
          'target_candidate':target.candidate,'target_evidence':target.model_dump(),
          'attack_instance_candidate':qualified,'attack_instance_basis':'context_with_grounded_target' if qualified else 'insufficient_context_or_target',
          'rule_version':RULE_VERSION,'lexicon_version':LEXICON_VERSION,'needs_human_review':context.needs_human_review or row['review_recommended']}
        if context.attack_candidate and grounded:
            history[comment.user_id].append(target.candidate);history_ids[comment.user_id].append(comment.comment_id)
        if qualified:
            pairs[(comment.user_id,target.candidate)].append((comment,target));grounded_instances.append((comment,target))
        row['review_recommended']|=row['analysis_signals']['needs_human_review']
    # Resolve an otherwise ungrounded root attack only from a bounded reciprocal
    # exchange. Keep reply/context evidence separate from attack-instance evidence.
    for row in data['comments']:
        comment=by_id[row['comment_id']];context=contexts[comment.comment_id]
        if targets[comment.comment_id].candidate is not None or not context.attack_candidate:continue
        target=resolve_root_exchange(comment,by_id,context,grounded_instances,contexts)
        if target.candidate is None:continue
        row['directed_at_user_id']=target.candidate
        row['analysis_signals'].update(target_candidate=target.candidate,target_evidence=target.model_dump(),
            attack_instance_candidate=True,attack_instance_basis='context_with_grounded_target')
        pairs[(comment.user_id,target.candidate)].append((comment,target))
    evidence=[]
    for (actor,target),rows in sorted(pairs.items()):
        rows.sort(key=lambda item:(item[0].timestamp,item[0].comment_id))
        times={c.timestamp.astimezone(timezone.utc).isoformat() for c,_ in rows}
        if len(rows)<2 or len(times)<2:continue
        evidence.append({'actor_user_id':actor,'target_user_id':target,'evidence_comment_ids':[c.comment_id for c,_ in rows],
          'n_distinct_timestamps':len(times),'target_confidence':'medium' if any(t.confidence=='medium' for _,t in rows) else 'high'})
    data['evidence']=evidence;data['suspected_repeated_harassment']=bool(evidence)
    data['risk_level']='suspected_repeated' if evidence else 'needs_review' if any(c['review_recommended'] for c in data['comments']) else 'none'
    data['risk_score_heuristic']=min(95,65+5*max(len(e['evidence_comment_ids']) for e in evidence)) if evidence else 35 if data['risk_level']=='needs_review' else 0
    data.update(analysis_version=ANALYSIS_VERSION,rule_versions={'context':CONTEXT_VERSION,'target':TARGET_VERSION,'repeated':RULE_VERSION,'assessment':ASSESSMENT_VERSION},source_model_threshold=legacy.model_threshold,policy_executed=False,checkpoint_id=getattr(predictor,'name','unknown'))
    data['warnings'].append('Version 2 evidence uses context and grounded attack targets; legacy recipient fields are retained separately. Heuristics require human review, not a harassment verdict.')
    return data
