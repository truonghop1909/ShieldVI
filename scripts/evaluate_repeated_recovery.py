"""Paired rule ablations with immutable r06 scores and one-pass new synthetic audit."""
import argparse,importlib.util,json,os,sys
from pathlib import Path
from unittest.mock import patch
from datetime import datetime
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'services/moderation-ai'));sys.path.insert(0,str(ROOT/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
from evaluate_synthetic_signals import classification,grounding_metrics
from refine_model import metrics
from app.schemas import AnalyzeRequest,AnalyzeResponseV2
from app import signal_engine,context_signals,target_signals

def snapshot(directory,name):
    spec=importlib.util.spec_from_file_location('app.snapshot_'+name,directory/(name+'.py'))
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module

def stats(rows):
    result=classification(rows);n=result['n'];p=result['toxic_precision'];r=result['toxic_recall']
    result.update(accuracy=(result['tp']+result['tn'])/n if n else None,toxic_f1=2*p*r/(p+r) if p+r else 0,
        confusion_matrix=[[result['tn'],result['fp']],[result['fn'],result['tp']]],matrix_axes='rows reference CLEAN/TOXIC, columns prediction CLEAN/TOXIC; abstentions reported separately')
    return result

def main(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    if (out/'evaluation.json').exists():raise FileExistsError('Never overwrite a completed one-pass challenge')
    evidence=ROOT/'reports/ai_update/repeated_recovery_20261103';fresh=ROOT/'datasets/fixtures/repeated_holdout_20261103'
    lock=json.loads((evidence/'frozen_rule_lock.json').read_text())
    assert all(file_sha(ROOT/'services/moderation-ai/app'/name)==h for name,h in lock['rule_sha256'].items())
    fm=json.loads((fresh/'manifest.json').read_text(encoding='utf-8'))
    new=[]
    for tid,h in fm['thread_sha256'].items():
        path=fresh/(tid+'.json');assert file_sha(path)==h;new.append(json.loads(path.read_text(encoding='utf-8')))
    # Validate graph/timestamps and distinct participants before first inference.
    for t in new:
        AnalyzeRequest.model_validate(t);assert 3<=len({c['user_id'] for c in t['comments']})<=6
    old=ROOT/'reports/ai_update/synthetic_experiment_r06_20261103/evaluation'
    cache=json.loads((old/'predictions.json').read_text(encoding='utf-8'))
    scores={name:{} for name in ('V1','r05','r06')}
    for row in cache:scores[row['model']][(row['thread_id'],row['comment_id'])]=row['raw_score']
    prior=[json.loads(line) for name in ('validation_threads.jsonl','challenge_threads.jsonl') for line in (ROOT/'datasets/synthetic_genz'/name).read_text(encoding='utf-8').splitlines()]
    for t in new:t['split']='fresh_synthetic_challenge'
    texts=[c['text'] for t in new for c in t['comments']]
    atomic_json(out/'evaluation_lock.json',{'rules':lock,'fresh_manifest_sha256':file_sha(fresh/'manifest.json'),
        'cached_predictions_sha256':file_sha(old/'predictions.json'),'training_performed':False,'human_gold':False,
        'one_pass_no_post_score_rule_tuning':True,'fresh_comments':len(texts),'real_world_metrics':False})
    scorefile=out/'fresh_scores.json'
    cfg=json.loads((ROOT/'configs/t029_synthetic_only_cpu_r06.json').read_text());tr=json.loads((Path(cfg['output_dir'])/'training_report.json').read_text())
    paths={'V1':Path(json.loads((evidence.parent/'synthetic_experiment_r06_20261103/prepared/manifest.json').read_text())['base_model_path']),
        'r05':ROOT/'models/candidates/T029_genz500_head_cpu_20261103_r05','r06':Path(cfg['output_dir'])}
    model_hashes={name:file_sha(path/'model.safetensors') for name,path in paths.items()}
    assert model_hashes['r06']==tr['candidate_sha256']
    if scorefile.exists():
        sc=json.loads(scorefile.read_text());assert sc['manifest_sha256']==file_sha(fresh/'manifest.json') and sc['model_sha256']==model_hashes
    else:
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0')
        import torch
        torch.set_num_threads(4)
        from app.predictor import ViSoBERTPredictor
        fresh_scores={}
        for name,path in paths.items():
            model=ViSoBERTPredictor(str(path));assert model.threshold==.41
            fresh_scores[name]=model.predict_scores(texts);del model
        sc={'manifest_sha256':file_sha(fresh/'manifest.json'),'model_sha256':model_hashes,'actual_inference':True,
            'training_performed':False,'max_length':128,'scores':fresh_scores};atomic_json(scorefile,sc)
    for name,values in sc['scores'].items():
        assert len(values)==len(texts)
        for c,score in zip([c for t in new for c in t['comments']],values):scores[name][(c['comment_id'].rsplit('_c',1)[0],c['comment_id'])]=score
    beforectx=snapshot(evidence/'before_sources','context_signals');beforetarget=snapshot(evidence/'before_sources','target_signals');beforeengine=snapshot(evidence/'before_sources','signal_engine')
    variants={'before':(beforeengine,beforectx,beforetarget),'context_only':(beforeengine,context_signals,beforetarget),
        'target_repeated_only':(signal_engine,beforectx,target_signals),'after':(signal_engine,context_signals,target_signals)}
    outputs={};summary={};truth={};all_threads=prior+new
    for t in all_threads:
        for c in t['comments']:
            a=c.get('annotation',c);truth[(t['thread_id'],c['comment_id'])]={'label':a['label'],'actor':c['user_id'],
                'target':a['directed_at_user_id'] if a['is_directed_attack'] else None,'time':c['timestamp']}
    for name in scores:
        outputs[name]={};summary[name]={}
        for variant,(engine,ctx,target) in variants.items():
            result=[]
            for t in all_threads:
                mapping={c['text']:scores[name][(t['thread_id'],c['comment_id'])] for c in t['comments']}
                class Cached:
                    threshold=.41;name='actual_model_scores_cached'
                    def predict_scores(self,texts):return [mapping[text] for text in texts]
                payload=AnalyzeRequest.model_validate({'thread_id':t['thread_id'],'comments':[{k:c[k] for k in ('comment_id','user_id','parent_id','timestamp','text')} for c in t['comments']]})
                with patch.object(engine,'analyze_context',ctx.analyze_context),patch.object(engine,'infer_target',target.infer_target),patch.object(engine,'CONTEXT_VERSION',ctx.VERSION),patch.object(engine,'TARGET_VERSION',target.VERSION):
                    value=engine.analyze_thread_v2(payload,Cached())
                    AnalyzeResponseV2.model_validate(value)
                result.append({'output':value,'split':t['split']})
            outputs[name][variant]=result;summary[name][variant]={}
            for split in ('synthetic_validation','synthetic_challenge','fresh_synthetic_challenge'):
                subset=[x for x in result if x['split']==split];labels={k:v for k,v in truth.items() if k[0] in {x['output']['thread_id'] for x in subset}}
                rows=[(labels[(item['output']['thread_id'],c['comment_id'])]['label'],c['moderation_assessment']['label']) for item in subset for c in item['output']['comments']]
                grounding=grounding_metrics(subset,labels)
                evidence_valid=[]
                for item in subset:
                    tid=item['output']['thread_id']
                    for e in item['output']['evidence']:
                        ids=e['evidence_comment_ids'];refs=[labels.get((tid,cid)) for cid in ids]
                        valid=len(ids)>=2 and len(ids)==len(set(ids)) and all(v and v['label']=='TOXIC' and v['actor']==e['actor_user_id'] and v['target']==e['target_user_id'] for v in refs)
                        valid=valid and len({datetime.fromisoformat(v['time']) for v in refs})>=2
                        evidence_valid.append(bool(valid))
                summary[name][variant][split]={'classification':stats(rows),'grounding':grounding,
                    'fully_supported_events':sum(evidence_valid),'emitted_events':len(evidence_valid),'all_emitted_evidence_valid':all(evidence_valid)}
        # Raw/legacy fields must be identical for every module ablation.
        fields=('toxicity_score','toxic_for_moderation','toxic_for_repeated_rule','target_user_id','target_method','target_confidence','lexical_signals')
        for variant,result in outputs[name].items():
            for before,after in zip(outputs[name]['before'],result):
                for a,b in zip(before['output']['comments'],after['output']['comments']):assert all(a[k]==b[k] for k in fields)
        summary[name]['raw']={}
        for split in ('synthetic_validation','synthetic_challenge','fresh_synthetic_challenge'):
            rows=[(truth[(t['thread_id'],c['comment_id'])]['label'],scores[name][(t['thread_id'],c['comment_id'])]) for t in all_threads if t['split']==split for c in t['comments']]
            summary[name]['raw'][split]=stats([(label,'TOXIC' if score>=.41 else 'CLEAN') for label,score in rows])
    # A fresh challenge is never used to change these locked sources.
    assert all(file_sha(ROOT/'services/moderation-ai/app'/name)==h for name,h in lock['rule_sha256'].items())
    result={'status':'COMPLETE_SYNTHETIC_ONLY','metrics':summary,'raw_invariant':True,'threshold':.41,'human_gold':False,
        'training_performed':False,'new_model_created':False,'default_changed':False,'historical_test_scored':False,
        'fresh_challenge_comments':len(texts),'fresh_model_scores':'actual local inference; prior620scores from immutable r06 cache',
        'ablation':'Context-only vs target/repeated-only vs full; lexicon unchanged and held fixed. Not retraining ablations.',
        'rule_lock_sha256':file_sha(evidence/'frozen_rule_lock.json'),'limitations':['All reference labels AI-authored.','Previously seen60threads are development regression.','Fresh12 authored by same assistant after rule freeze; not human/author blind.','No rule edits allowed after fresh scores; report errors without tuning.']}
    atomic_json(out/'outputs.json',outputs);atomic_json(out/'evaluation.json',result)
    print(json.dumps({'status':result['status'],'r06_repeated':{s:summary['r06']['after'][s]['grounding']['repeated'] for s in ('synthetic_challenge','fresh_synthetic_challenge')}}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.output)
