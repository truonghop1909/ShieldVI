"""Paired v6.1/v6.2 research replay, invariant raw caches and original labels."""
import argparse,json,sys,csv
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(R/'services/moderation-ai'))
from app.schemas import AnalyzeRequest,AnalyzeResponseV2
from app.experiments.fresh10_v6 import analyze_thread_v6
from app.experiments.research_v62 import analyze_thread_v62
from evaluate_fresh10_recovery import fresh_items,evidence_metrics
from evaluate_context_recovery import load_inputs
from evaluate_synthetic_signals import classification,grounding_metrics,target_truth
from synthetic_data.pipeline import atomic_json,file_sha

def evaluate(items,truth,events=()):
    before=[];after=[];rows=[]
    for item in items:
        payload=AnalyzeRequest.model_validate(item['payload']);mapping=dict(zip([c.text for c in payload.comments],item['scores']))
        class Cache:
            threshold=.41;name='frozen_actual_score_cache'
            def predict_scores(self,texts):return [mapping[t] for t in texts]
        old=analyze_thread_v6(payload,Cache());new=analyze_thread_v62(payload,Cache());AnalyzeResponseV2.model_validate(new)
        before.append({'output':old});after.append({'output':new})
        for c,a,b in zip(payload.comments,old['comments'],new['comments']):
            for key in ('toxicity_score','toxic_for_moderation','toxic_for_repeated_rule','target_user_id','target_method','target_confidence','lexical_signals'):
                assert a[key]==b[key],(payload.thread_id,c.comment_id,key)
            ref=truth.get((payload.thread_id,c.comment_id),{}).get('label',item.get('labels',{}).get(c.comment_id))
            assert ref in ('CLEAN','TOXIC','UNCERTAIN')
            rows.append({'thread_id':payload.thread_id,'comment_id':c.comment_id,'text':c.text,'reference':ref,'raw_score':b['toxicity_score'],
                'before':a['moderation_assessment']['label'],'after':b['moderation_assessment']['label'],'before_target':a['directed_at_user_id'],'after_target':b['directed_at_user_id']})
    metrics={'comments':len(rows),'classification':{phase:classification([(r['reference'],r[phase]) for r in rows]) for phase in ('before','after')},
        'grounding':{'before':grounding_metrics(before,truth),'after':grounding_metrics(after,truth)},
        'new_label_errors':[r for r in rows if r['reference']!='UNCERTAIN' and r['before']==r['reference'] and r['after']!=r['reference']],
        'remaining_errors':[r for r in rows if r['reference']!='UNCERTAIN' and r['after']!=r['reference']],
        'changed_comments':[r for r in rows if r['before']!=r['after'] or r['before_target']!=r['after_target']],
        'raw_invariant':True,'human_gold':False,'training_performed':False,'before_processor':'v6.1','after_processor':'v6.2'}
    if events:metrics['reference_evidence']={'before':evidence_metrics(before,events),'after':evidence_metrics(after,events)}
    return metrics,before,after,rows

def annotated(folder,cachefile):
    folder=Path(folder);meta=json.loads((folder/'manifest.json').read_text());cache=json.loads(Path(cachefile).read_text())
    assert file_sha(folder/'manifest.json')==cache['manifest_sha256']
    threads=[]
    for tid,digest in meta['thread_sha256'].items():
        path=(folder/'threads'/(tid+'.json')) if (folder/'threads').exists() else folder/(tid+'.json')
        assert file_sha(path)==digest;threads.append(json.loads(path.read_text()))
    cached=cache['scores']
    if isinstance(cached,dict) and 'r06' in cached:cached=cached['r06']
    items=[];truth={};events=[];offset=0
    for t in threads:
        n=len(t['comments']);scores=cached[t['thread_id']] if isinstance(cached,dict) else cached[offset:offset+n];offset+=n
        items.append({'payload':{'thread_id':t['thread_id'],'comments':[{k:c.get(k) for k in ('comment_id','parent_id','user_id','timestamp','text')} for c in t['comments']]},'scores':scores})
        pairs=defaultdict(list)
        for c in t['comments']:
            a=c['annotation'];truth[(t['thread_id'],c['comment_id'])]={'label':a['label'],'actor':c['user_id'],'target':a['directed_at_user_id'],'time':c['timestamp']}
            if a['label']=='TOXIC' and a['directed_at_user_id']:pairs[(c['user_id'],a['directed_at_user_id'])].append(c['comment_id'])
        for (actor,target),ids in pairs.items():
            if len(ids)>=2:events.append({'thread_id':t['thread_id'],'actor_user_id':actor,'target_user_id':target,'expected_repeated':'true','evidence_comment_ids':';'.join(ids)})
    return items,truth,events

def write_cohort(output,name,items,truth,events=()):
    metrics,before,after,rows=evaluate(items,truth,events)
    for suffix,value in [('metrics',metrics),('before',before),('after',after),('rows',rows)]:atomic_json(output/name/(suffix+'.json'),value)
    return metrics

def run(output):
    if output.exists():raise FileExistsError('Keep older evidence; use a new output revision')
    results={}
    for name in ('fresh10','nov10'):
        folder=R/'datasets/fixtures'/(name+'_regression_v1');items,truth=fresh_items(folder)
        events=list(csv.DictReader((folder/'expected_repeated_events.csv').open(encoding='utf-8-sig')))
        results[name]=write_cohort(output,name,items,truth,events)
    old=load_inputs();cache=json.loads((R/'reports/ai_update/context_recovery_20261103/score_cache.json').read_text())
    results['old890']=write_cohort(output,'old890',[{**x,'scores':cache[x['payload']['thread_id']]} for x in old],target_truth())
    small=[('postfix48','fresh10_postfix_holdout_v1','fresh10_recovery_20261103/postfix_scores.json'),
        ('postfix24','fresh10_postfix_holdout_v2','fresh10_recovery_20261103/final_scores.json'),
        ('nov_audit24','nov10_audit_challenge_v1','nov10_audit_20261104/challenge_scores.json'),
        ('repeated74','repeated_holdout_20261103','repeated_recovery_20261103/evaluation/fresh_scores.json')]
    for name,data,scores in small:results[name]=write_cohort(output,name,*annotated(R/'datasets/fixtures'/data,R/'reports/ai_update'/scores))
    atomic_json(output/'summary.json',{name:{k:r[k] for k in ('classification','grounding','new_label_errors')} for name,r in results.items()})
    print(json.dumps({name:{'f1_before':r['classification']['before']['macro_f1'],'f1_after':r['classification']['after']['macro_f1'],
        'new_errors':len(r['new_label_errors']),'target':r['grounding']['after']['target_correct'],'repeated':r['grounding']['after']['repeated']['tp']} for name,r in results.items()}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.output)
