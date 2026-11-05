"""Paired cached-inference regression: compare advisory outputs, not just raw badges."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
from evaluate_context_recovery import load_inputs,evaluate,stats
lock=json.loads((P/'before_lock.json').read_text(encoding='utf-8'))
assert file_sha(P/'before.json')==lock['before_sha256']
assert file_sha(R/'tests/fixtures/ai_update/camping_reference.json')==lock['reference_sha256']
scorefile=R/'reports/ai_update/context_recovery_20261103/score_cache.json'
assert file_sha(scorefile)==lock['baseline_scores_sha256']
scores=json.loads(scorefile.read_text(encoding='utf-8'))
before=json.loads((P/'before.json').read_text(encoding='utf-8'));after=evaluate(load_inputs(),scores)
atomic_json(P/'after.json',after)
paired=[];events=[]
for left,right in zip(before,after):
    assert left['labels']==right['labels'] and left['output']['thread_id']==right['output']['thread_id']
    tid=left['output']['thread_id']
    for a,b in zip(left['output']['comments'],right['output']['comments']):
        for key in ('comment_id','toxicity_score','toxic_for_moderation','toxic_for_repeated_rule','target_user_id','target_method','target_confidence'):
            assert a[key]==b[key],(tid,key)
        paired.append({'group':left['group'],'thread_id':tid,'comment_id':a['comment_id'],'reference':left['labels'][a['comment_id']],
          'raw':'TOXIC' if a['toxic_for_moderation'] else 'CLEAN','before':a['moderation_assessment']['label'],'after':b['moderation_assessment']['label'],
          'before_attack':a['analysis_signals']['attack_instance_candidate'],'after_attack':b['analysis_signals']['attack_instance_candidate'],
          'before_context':a['analysis_signals']['context_tags'],'after_context':b['analysis_signals']['context_tags']})
    if left['output']['evidence']!=right['output']['evidence']:
        old={(e['actor_user_id'],e['target_user_id']):set(e['evidence_comment_ids']) for e in left['output']['evidence']}
        newly_bad=[]
        for e in right['output']['evidence']:
            added=set(e['evidence_comment_ids'])-old.get((e['actor_user_id'],e['target_user_id']),set())
            newly_bad += [cid for cid in added if right['labels'][cid]=='CLEAN']
        events.append({'thread_id':tid,'before':left['output']['evidence'],'after':right['output']['evidence'],'new_evidence_with_CLEAN_reference':sorted(newly_bad)})
regressions=[r for r in paired if r['reference']!='UNCERTAIN' and r['before']==r['reference'] and r['after']!=r['reference']]
improvements=[r for r in paired if r['reference']!='UNCERTAIN' and r['before']!=r['reference'] and r['after']==r['reference']]
result={'human_gold':False,'independent_test_scored':False,'real_inference_source':'Original V1 frozen CPU scores, reused identically; live V1.1/r05 tested separately',
 'comments':len(paired),'raw_invariant':True,'groups':{g:{field:stats([r for r in paired if r['group']==g],field) for field in ('raw','before','after')} for g in sorted({r['group'] for r in paired})},
 'new_errors_or_abstentions':regressions,'new_errors_count':len(regressions),'improved_assessments':improvements,
 'changed_assessments':[r for r in paired if r['before']!=r['after']],'event_changes':events,
 'new_clean_reference_event_evidence':[e for e in events if e['new_evidence_with_CLEAN_reference']],
 'limitations':['Previously viewed synthetic development, not a blind test.','CLEAN reference checks do not establish target correctness or real-world harassment accuracy.']}
atomic_json(P/'before_after.json',result);atomic_json(P/'paired_comments.json',paired)
print(json.dumps({'comments':len(paired),'raw_unchanged':True,'improved_assessments':len(improvements),
  'new_errors':len(regressions),'event_changes':len(events),'new_clean_reference_event_evidence':len(result['new_clean_reference_event_evidence'])}))
