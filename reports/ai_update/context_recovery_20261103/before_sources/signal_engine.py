"""Versioned analysis pipeline; legacy engine remains available for API 0.3 consumers."""
from collections import defaultdict
import hashlib
from .lexical import DATA_DIR
LEXICON_VERSION=hashlib.sha256((DATA_DIR/"active.json").read_bytes()).hexdigest()
from datetime import timezone
from .engine import analyze_thread
from .context_signals import analyze_context,VERSION as CONTEXT_VERSION
from .target_signals import infer_target,VERSION as TARGET_VERSION
RULE_VERSION='repeated-v3'
ANALYSIS_VERSION='2.0'

def analyze_thread_v2(payload,predictor):
    legacy=analyze_thread(payload,predictor)
    data=legacy.model_dump(mode='json')
    by_id={c.comment_id:c for c in payload.comments}
    history=defaultdict(list);history_ids=defaultdict(list);pairs=defaultdict(list)
    for row in data['comments']:
        comment=by_id[row['comment_id']]
        context=analyze_context(comment.text)
        target=infer_target(comment,by_id,context,history[comment.user_id],history_ids[comment.user_id])
        grounded=target.candidate is not None and target.confidence in ('medium','high')
        qualified=bool(context.attack_candidate and grounded and row['toxic_for_repeated_rule'])
        row['analysis_signals']={'context_tags':context.tags,'context':context.model_dump(),
          'directed_attack_candidate':context.attack_candidate,'attack_confidence':context.confidence,
          'target_candidate':target.candidate,'target_evidence':target.model_dump(),
          'attack_instance_candidate':qualified,'rule_version':RULE_VERSION,'lexicon_version':LEXICON_VERSION,'needs_human_review':context.needs_human_review or row['review_recommended']}
        if context.attack_candidate and grounded:
            history[comment.user_id].append(target.candidate);history_ids[comment.user_id].append(comment.comment_id)
        if qualified:pairs[(comment.user_id,target.candidate)].append((comment,target))
        row['review_recommended']|=row['analysis_signals']['needs_human_review']
    evidence=[]
    for (actor,target),rows in sorted(pairs.items()):
        times={c.timestamp.astimezone(timezone.utc).isoformat() for c,_ in rows}
        if len(rows)<2 or len(times)<2:continue
        evidence.append({'actor_user_id':actor,'target_user_id':target,'evidence_comment_ids':[c.comment_id for c,_ in rows],
          'n_distinct_timestamps':len(times),'target_confidence':'medium' if any(t.confidence=='medium' for _,t in rows) else 'high'})
    data['evidence']=evidence;data['suspected_repeated_harassment']=bool(evidence)
    data['risk_level']='suspected_repeated' if evidence else 'needs_review' if any(c['review_recommended'] for c in data['comments']) else 'none'
    data['risk_score_heuristic']=min(95,65+5*max(len(e['evidence_comment_ids']) for e in evidence)) if evidence else 35 if data['risk_level']=='needs_review' else 0
    data.update(analysis_version=ANALYSIS_VERSION,rule_versions={'context':CONTEXT_VERSION,'target':TARGET_VERSION,'repeated':RULE_VERSION},source_model_threshold=legacy.model_threshold,policy_executed=False,checkpoint_id=getattr(predictor,'name','unknown'))
    data['warnings'].append('Version 2 evidence uses context and grounded attack targets; legacy recipient fields are retained separately. Heuristics require human review, not a harassment verdict.')
    return data
