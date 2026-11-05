"""Offline opt-in evaluation of imported synthetic references; no training or promotion."""
import argparse,csv,json,sys
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'services/moderation-ai'));sys.path.insert(0,str(R/'scripts'))
from app.schemas import AnalyzeRequest,AnalyzeResponseV2
from app.signal_engine import analyze_thread_v2
from app.experiments.fresh10_v6 import analyze_thread_v6
from synthetic_data.pipeline import atomic_json,file_sha
from evaluate_synthetic_signals import classification,grounding_metrics,target_truth
from evaluate_context_recovery import load_inputs

def evidence_metrics(outputs,events):
    wanted={(e['thread_id'],e['actor_user_id'],e['target_user_id']):set(e['evidence_comment_ids'].split(';')) for e in events if e['expected_repeated']=='true'}
    emitted={(x['output']['thread_id'],e['actor_user_id'],e['target_user_id']):set(e['evidence_comment_ids']) for x in outputs for e in x['output']['evidence']}
    correct=sum(len(ids&wanted.get(key,set())) for key,ids in emitted.items());total=sum(map(len,emitted.values()));expected=sum(map(len,wanted.values()))
    return {'evidence_correct':correct,'evidence_emitted':total,'evidence_reference':expected,'evidence_precision':correct/total if total else 0,
        'evidence_recall':correct/expected if expected else 0,'fully_covered_events':sum(key in emitted and ids<=emitted[key] for key,ids in wanted.items()),
        'expected_events':len(wanted),'missing_evidence':[{ 'pair':list(key),'missing':sorted(ids-emitted.get(key,set()))} for key,ids in wanted.items() if ids-emitted.get(key,set())]}

def fresh_items(directory):
    refs=list(csv.DictReader((directory/'expected_reference_labels.csv').open(encoding='utf-8-sig',newline='')));truth={};items=[]
    labels={(r['thread_id'],r['comment_id']):r for r in refs}
    imports={x['thread_id']:x for x in [json.loads(p.read_text(encoding='utf-8-sig')) for p in (directory/'analysis').glob('*.json')]}
    for p in sorted((directory/'inputs').glob('*.json')):
        t=json.loads(p.read_text(encoding='utf-8-sig'));out=imports[t['thread_id']]
        scores={c['comment_id']:c['toxicity_score'] for c in out['comments']}
        items.append({'payload':t,'scores':[scores[c['comment_id']] for c in t['comments']],'before':out})
        for c in t['comments']:
            a=labels[(t['thread_id'],c['comment_id'])];truth[(t['thread_id'],c['comment_id'])]={'label':a['expected_label'],'actor':c['user_id'],
                'target':a['directed_at_user_id'] if a['is_directed_attack']=='true' else None,'time':c['timestamp']}
    return items,truth

def replay(items,truth):
    before=[];after=[];rows=[]
    for item in items:
        t=item['payload'];mapping=dict(zip([c['text'] for c in t['comments']],item['scores']))
        class Cached:
            threshold=.41;name='imported_actual_scores_cached_no_new_forward'
            def predict_scores(self,texts):return [mapping[text] for text in texts]
        payload=AnalyzeRequest.model_validate(t);old=item.get('before') or analyze_thread_v2(payload,Cached());new=analyze_thread_v6(payload,Cached())
        old=json.loads(json.dumps(old));new=json.loads(json.dumps(new));AnalyzeResponseV2.model_validate(new)
        before.append({'output':old});after.append({'output':new})
        for c,a,b in zip(t['comments'],old['comments'],new['comments']):
            for key in ('comment_id','toxicity_score','toxic_for_moderation','toxic_for_repeated_rule','target_user_id','target_method','target_confidence','lexical_signals'):
                assert a[key]==b[key],(t['thread_id'],c['comment_id'],key)
            reference=truth[(t['thread_id'],c['comment_id'])]['label'] if (t['thread_id'],c['comment_id']) in truth else item['labels'][c['comment_id']]
            rows.append({'thread_id':t['thread_id'],'comment_id':c['comment_id'],'text':c['text'],'reference':reference,'before':a['moderation_assessment']['label'],
                'after':b['moderation_assessment']['label'],'raw_score':b['toxicity_score'],'before_target':a['directed_at_user_id'],'after_target':b['directed_at_user_id']})
    result={'classification':{phase:classification([(r['reference'],r[phase]) for r in rows]) for phase in ('before','after')},
        'grounding':{'before':grounding_metrics(before,truth),'after':grounding_metrics(after,truth)},'comments':len(rows),'raw_invariant':True,
        'new_label_errors':[r for r in rows if r['reference']!='UNCERTAIN' and r['before']==r['reference'] and r['after']!=r['reference']],
        'remaining_errors':[r for r in rows if r['reference']!='UNCERTAIN' and r['after']!=r['reference']],
        'changed_comments':[r for r in rows if r['before']!=r['after'] or r['before_target']!=r['after_target']],
        'uncertain_reference_excluded':sum(r['reference']=='UNCERTAIN' for r in rows)}
    return result,before,after,rows

def run(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Keep prior evidence; use a new output revision')
    directory=R/'datasets/fixtures/fresh10_regression_v1';manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    for name,h in manifest['files'].items():assert file_sha(directory/name)==h
    items,truth=fresh_items(directory);result,before,after,rows=replay(items,truth)
    events=list(csv.DictReader((directory/'expected_repeated_events.csv').open(encoding='utf-8-sig',newline='')))
    result['reference_evidence']={'before':evidence_metrics(before,events),'after':evidence_metrics(after,events)}
    result.update(scope='Fresh10 development regression; imported user-r06 score cache only',human_gold=False,training_performed=False,default_changed=False,readiness_lock_modified=False)
    output.mkdir(parents=True);atomic_json(output/'fresh10_metrics.json',result);atomic_json(output/'fresh10_after.json',after);atomic_json(output/'fresh10_rows.json',rows)
    old_items=load_inputs();old_scores=json.loads((R/'reports/ai_update/context_recovery_20261103/score_cache.json').read_text(encoding='utf-8'))
    old_truth=target_truth();regression=[]
    for item in old_items:regression.append({**item,'scores':old_scores[item['payload']['thread_id']]})
    broad,before_b,after_b,rows_b=replay(regression,old_truth)
    broad.update(scope='Previously viewed890comment regression, originalV1 cached scores, not r06 classifier evaluation',human_gold=False)
    atomic_json(output/'old_regression_metrics.json',broad);atomic_json(output/'old_regression_after.json',after_b);atomic_json(output/'old_regression_rows.json',rows_b)
    print(json.dumps({'fresh10':{'classification':result['classification'],'grounding':result['grounding'],'evidence':result['reference_evidence']},
        'old_regression':{'classification':broad['classification'],'grounding':broad['grounding'],'new_label_errors':broad['new_label_errors']}}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
