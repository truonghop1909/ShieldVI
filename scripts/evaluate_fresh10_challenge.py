"""Evaluate a versioned annotated synthetic fixture with frozen r06 score cache.

An optional first CPU inference is offline, bounded to four threads; no training.
Never overwrites an output or changes reference labels.
"""
import argparse,json,os,sys
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(R/'services/moderation-ai'))
from synthetic_data.pipeline import atomic_json,file_sha
from evaluate_fresh10_recovery import replay,evidence_metrics


def run(dataset,scores,output,lock):
    if output.exists():raise FileExistsError('Retain earlier results; use a new revision')
    frozen=json.loads(lock.read_text(encoding='utf-8'))
    module=R/'services/moderation-ai/app/experiments/fresh10_v6.py'
    assert file_sha(module)==frozen['experimental_module_sha256']
    manifest=dataset/'manifest.json';metadata=json.loads(manifest.read_text(encoding='utf-8'))
    threads=[]
    for tid,digest in metadata['thread_sha256'].items():
        path=dataset/'threads'/(tid+'.json');assert file_sha(path)==digest
        threads.append(json.loads(path.read_text(encoding='utf-8')))
    cfg=json.loads((R/'configs/t029_synthetic_only_cpu_r06.json').read_text())
    model=Path(cfg['output_dir']);weights=file_sha(model/'model.safetensors')
    texts=[c['text'] for t in threads for c in t['comments']]
    if scores.exists():
        cache=json.loads(scores.read_text(encoding='utf-8'))
        assert cache['manifest_sha256']==file_sha(manifest) and cache['model_sha256']==weights
    else:
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0')
        import torch
        torch.set_num_threads(4)
        from app.predictor import ViSoBERTPredictor
        predictor=ViSoBERTPredictor(str(model));assert predictor.threshold==.41
        cache={'manifest_sha256':file_sha(manifest),'model_sha256':weights,
               'actual_r06_inference':True,'training_performed':False,'scores':predictor.predict_scores(texts)}
        atomic_json(scores,cache)
    assert len(cache['scores'])==len(texts)
    items=[];truth={};events=[];offset=0
    for thread in threads:
        payload={'thread_id':thread['thread_id'],'comments':[
            {k:c[k] for k in ('comment_id','parent_id','user_id','timestamp','text')} for c in thread['comments']]}
        items.append({'payload':payload,'scores':cache['scores'][offset:offset+len(thread['comments'])]})
        offset+=len(thread['comments']);pairs=defaultdict(list)
        for c in thread['comments']:
            a=c['annotation'];truth[(thread['thread_id'],c['comment_id'])]={
                'label':a['label'],'actor':c['user_id'],'target':a['directed_at_user_id'],'time':c['timestamp']}
            if a['label']=='TOXIC' and a['directed_at_user_id']:pairs[(c['user_id'],a['directed_at_user_id'])].append(c['comment_id'])
        for (actor,target),ids in pairs.items():
            if len(ids)>=2:events.append({'thread_id':thread['thread_id'],'actor_user_id':actor,'target_user_id':target,
                                         'expected_repeated':'true','evidence_comment_ids':';'.join(ids)})
    metrics,before,after,rows=replay(items,truth)
    metrics['reference_evidence']={'before':evidence_metrics(before,events),'after':evidence_metrics(after,events)}
    metrics.update(human_gold=False,training_performed=False,model_sha256=weights,
                   dataset_manifest_sha256=file_sha(manifest),experiment_lock_sha256=file_sha(lock),
                   scope='synthetic_reference; same author; no independent real-world evaluation')
    assert file_sha(module)==frozen['experimental_module_sha256'] and file_sha(model/'model.safetensors')==weights
    output.mkdir(parents=True)
    for name,value in [('metrics',metrics),('before',before),('after',after),('rows',rows)]:atomic_json(output/(name+'.json'),value)
    print(json.dumps({k:metrics[k] for k in ('classification','grounding','reference_evidence','new_label_errors')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('dataset','scores','output','lock'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();run(args.dataset,args.scores,args.output,args.lock)
