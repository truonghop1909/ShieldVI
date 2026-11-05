"""Actual candidate validation/final-test audit and local registry/shadow/rollback.
Never tunes on test, changes the default, or performs a production deployment.
"""
from __future__ import annotations
import argparse,copy,csv,json,os,sys,secrets,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from refine_model import read_rows,file_hash,metrics,validation_gate,test_gate
from synthetic_data.pipeline import atomic_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=ROOT/'configs/t029_genz500_cpu_head.json');a=p.parse_args()
    P=ROOT/'reports/ai_update/all_tasks_cpu_20261103';cfg=json.loads(a.config.read_text(encoding='utf-8'));candidate_path=Path(cfg['output_dir'])
    training=json.loads((candidate_path/'training_report.json').read_text(encoding='utf-8'))
    if training['status']!='COMPLETE_HEAD_TRAINED_NOT_ACTIVATED' or not training['encoder_unchanged'] or training['optimizer_steps']<1:raise ValueError('A verified actually-trained candidate is required')
    if file_hash(candidate_path/'model.safetensors')!=training['candidate_sha256']:raise ValueError('Candidate changed after selection')
    if (P/'candidate_evaluation.json').exists():raise FileExistsError('Preserve completed final-test audit; do not run selection again')
    protocol=json.loads((P/'evaluation_protocol.json').read_text(encoding='utf-8'))
    if file_hash(ROOT/'scripts/refine_model.py')!=protocol['gate_implementation_sha256']:raise ValueError('Evaluation gate changed after freeze')
    old_registry=json.loads((ROOT/'configs/model_registry.local.json').read_text(encoding='utf-8'))
    registry=copy.deepcopy(old_registry);registry.update(candidate_available=True,candidate_run_id=cfg['run_id'],production_default_changed=False,
      evaluation_status='PENDING_LOCAL_REVIEW',training_report_sha256=file_hash(candidate_path/'training_report.json'))
    registry['models']['candidate_cpu']={'path':str(candidate_path),'role':'candidate','threshold':.41,'approved_for_selection':False,
      'sha256':{n:file_hash(candidate_path/n) for n in ('model.safetensors','config.json','threshold_config.json','tokenizer_config.json','tokenizer.json','sentencepiece.bpe.model','special_tokens_map.json') if (candidate_path/n).is_file()},
      'training_strategy':'frozen_encoder_head_cpu','full_encoder_finetune':False}
    registry['rule_sha256']={str(p.relative_to(ROOT)):file_hash(p) for p in [ROOT/'services/moderation-ai/app'/name for name in ('context_signals.py','context_assessment.py','signal_engine.py','target_signals.py')]}
    registry_path=ROOT/'configs/model_registry.cpu_r03.local.json';atomic_json(registry_path,registry)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0')
    import torch;torch.set_num_threads(4)
    from app.model_registry import LocalModelRegistry,RegistryError
    from app.predictor import default_model_path
    from app.schemas import AnalyzeRequest,AnalyzeResponseV2
    from app.signal_engine import analyze_thread_v2
    from evaluate_context_recovery import load_inputs,stats
    started=time.monotonic();reg=LocalModelRegistry(registry_path);default_before=default_model_path()
    baseline,_=reg.load('v1');candidate,candidate_audit=reg.load('candidate_cpu',shadow=True)
    active,_=reg.load('v1_1')
    models={'original_V1':baseline,'existing_default_V1_1':active,'candidate_head_CPU':candidate}
    prepared=json.loads((ROOT/'reports/ai_update/T029/genz500_cpu_prepared/manifest.json').read_text(encoding='utf-8'))
    for item in prepared['sources'].values():
        if file_hash(Path(item['path']))!=item['sha256']:raise ValueError('Training/heldout source changed')
    # Test labels are opened only here, after training and validation model selection completed.
    datasets={'ViCTSD_validation':read_rows(ROOT/cfg['validation']),'ViCTSD_test_final_audit':read_rows(ROOT/cfg['test_text_only'])}
    from t029_cpu_head import encoder_sha
    encoder_hashes={mid:encoder_sha(model.model.roberta) for mid,model in models.items()}
    method={'name':'shared_identical_frozen_encoder_and_actual_heads','encoder_sha256':encoder_hashes,'numerical_full_forward_probes':{},'encoder_batches':0,'tokenizer_equality_checked_each_batch':True}
    def score_all(texts,stage):
        values={mid:[None]*len(texts) for mid in models};order=sorted(range(len(texts)),key=lambda i:len(texts[i]))
        with torch.no_grad():
            for start in range(0,len(order),32):
                ids=order[start:start+32];batch=[texts[i] for i in ids]
                encodings={mid:model.tokenizer(batch,padding=True,truncation=True,max_length=cfg['max_length'],return_tensors='pt') for mid,model in models.items()}
                shared=[]
                for mid,model in models.items():
                    tokens=encodings[mid];feature=None
                    for sha,encoding,cached in shared:
                        if sha==encoder_hashes[mid] and set(encoding)==set(tokens) and all(torch.equal(encoding[k],tokens[k]) for k in tokens):feature=cached;break
                    if feature is None:
                        feature=model.model.roberta(**tokens).last_hidden_state[:,0,:]
                        shared.append((encoder_hashes[mid],tokens,feature));method['encoder_batches']+=1
                    scores=model.model.classifier(feature[:,None,:]).softmax(-1)[:,1].tolist()
                    for index,value in zip(ids,scores):values[mid][index]=float(value)
                if start%256==0 or start+32>=len(order):
                    atomic_json(P/'evaluation_progress.json',{'stage':stage,'rows':min(start+32,len(order)),'total':len(order),'elapsed_seconds':round(time.monotonic()-started,2)})
                    print(json.dumps({'stage':stage,'rows':min(start+32,len(order)),'total':len(order)}),flush=True)
        method['numerical_full_forward_probes'][stage]={}
        for mid,model in models.items():
            actual=model.predict_scores(texts[:3]);error=max(abs(v-values[mid][i]) for i,v in enumerate(actual))
            if error>1e-5:raise AssertionError('Shared encoder method disagrees with actual full forward')
            method['numerical_full_forward_probes'][stage][mid]=error
        return values

    results={};predictions=[]
    for name,rows in datasets.items():
        results[name]={}
        shared_values=score_all([r['text'] for r in rows],name)
        for model_id,model in models.items():
            values=shared_values[model_id]
            result=metrics([r['label'] for r in rows],values,.41);results[name][model_id]=result
            predictions.extend({'dataset':name,'model':model_id,'row_id':r['id'],'reference':r['label'],'score':s} for r,s in zip(rows,values))
            atomic_json(P/'evaluation_progress.json',{'stage':name,'model':model_id,'rows':len(rows),'elapsed_seconds':round(time.monotonic()-started,2)})
            print(json.dumps({'stage':name,'model':model_id,'n':result['n'],'macro_f1':result['macro_f1'],'precision':result['toxic_precision'],'recall':result['toxic_recall']}),flush=True)
    if abs(results['ViCTSD_validation']['candidate_head_CPU']['macro_f1']-training['candidate_validation']['macro_f1'])>1e-5:raise AssertionError('Reloaded full model disagrees with validation selection')
    paired=[];event_counts={}
    inputs=load_inputs()
    all_texts=[c['text'] for item in inputs for c in item['payload']['comments']]
    all_scores=score_all(all_texts,'already_viewed_synthetic_development')
    for model_id,model in models.items():
        score_by_text=dict(zip(all_texts,all_scores[model_id]))
        class CachedModel:
            threshold=model.threshold;name=model.name
            def predict_scores(self,texts):return [score_by_text[text] for text in texts]
        cached_model=CachedModel()
        event_counts[model_id]={};groups=[]
        for item in inputs:
            payload=AnalyzeRequest.model_validate(item['payload']);data=AnalyzeResponseV2.model_validate(analyze_thread_v2(payload,cached_model)).model_dump(mode='json')
            event_counts[model_id][payload.thread_id]=data['evidence']
            for row in data['comments']:
                paired.append({'group':item['group'],'thread_id':payload.thread_id,'comment_id':row['comment_id'],'reference':item['labels'][row['comment_id']],
                   'model':model_id,'raw_label':'TOXIC' if row['toxic_for_moderation'] else 'CLEAN','raw_score':row['toxicity_score'],
                   'assessment':row['moderation_assessment']['label'],'directed_target':row['directed_at_user_id']})
        print(json.dumps({'stage':'already_viewed_synthetic_development','model':model_id,'comments':sum(len(i['payload']['comments']) for i in inputs)}),flush=True)
    synthetic={g:{mid:{'raw':stats([r for r in paired if r['group']==g and r['model']==mid],'raw_label'),
         'assessment':stats([r for r in paired if r['group']==g and r['model']==mid],'assessment')} for mid in models} for g in sorted({r['group'] for r in paired})}
    val=results['ViCTSD_validation'];test=results['ViCTSD_test_final_audit']
    gates={'validation_vs_original':validation_gate(val['original_V1'],val['candidate_head_CPU']),
           'test_vs_original':test_gate(test['original_V1'],test['candidate_head_CPU']),
           'validation_vs_existing_default':validation_gate(val['existing_default_V1_1'],val['candidate_head_CPU']),
           'test_vs_existing_default':test_gate(test['existing_default_V1_1'],test['candidate_head_CPU'])}
    index={(r['model'],r['thread_id'],r['comment_id']):r for r in paired}
    regressions=[]
    for row in [r for r in paired if r['model']=='candidate_head_CPU' and r['reference']!='UNCERTAIN']:
        old=index[('original_V1',row['thread_id'],row['comment_id'])]
        if old['assessment']==row['reference'] and row['assessment']!=row['reference']:regressions.append(row)
    game_reference=json.loads((ROOT/'datasets/fixtures/context_recovery_v1/game_rank_30_reference.json').read_text(encoding='utf-8'))
    tid=game_reference['thread_id'];expected=game_reference['expected_repeated'];candidate_events=event_counts['candidate_head_CPU'][tid]
    gates['GAME_all_user_advisory_labels']=all(r['assessment']==r['reference'] for r in paired if r['model']=='candidate_head_CPU' and r['group']=='GAME_USER_REFERENCE')
    gates['GAME_exact_repeated_evidence']=any(e['actor_user_id']==expected['actor_user_id'] and e['target_user_id']==expected['target_user_id'] and e['evidence_comment_ids']==expected['evidence_comment_ids'] for e in candidate_events)
    gates['no_new_synthetic_advisory_errors']=not regressions
    decision='APPROVE_LOCAL_SHADOW_ONLY' if all(gates.values()) else 'REJECT_PROMOTION_KEEP_EXISTING_DEFAULT' 
    # Exercise local load refusal, deliberate candidate-load failure, V1 fallback and rollback.
    try:reg.load('candidate_cpu');raise AssertionError('Unapproved candidate selected without shadow')
    except RegistryError:pass
    def injected_failure(path):
        if Path(path).resolve()==candidate_path.resolve():raise RuntimeError('Deliberate shadow primary-load fault')
        if Path(path).resolve()==Path(reg.models['v1']['path']).resolve():return baseline
        raise AssertionError('Unexpected fallback model')
    recovered,fallback=reg.load('candidate_cpu',shadow=True,loader=injected_failure)
    restored,rollback=reg.load('v1',loader=lambda path:baseline)
    assert recovered is baseline and restored is baseline and fallback['fallback_used']
    from fastapi.testclient import TestClient
    from app.main import app
    probe=json.loads((ROOT/'datasets/fixtures/context_recovery_v1/game_rank_30_reference.json').read_text(encoding='utf-8'))
    payload=json.loads((ROOT/probe['input_file']).read_text(encoding='utf-8'))
    previous_env=os.environ.get('MODEL_PATH');token=secrets.token_urlsafe(32);os.environ['AI_SERVICE_TOKEN']=token
    try:
        app.state.predictor=candidate;app.state.error=None;os.environ['MODEL_PATH']=str(candidate_path)
        with_no_lifespan=TestClient(app)
        old=with_no_lifespan.post('/api/analyze',json=payload);new=with_no_lifespan.post('/api/v2/analyze',json=payload)
        assert old.status_code==new.status_code==200
        AnalyzeResponseV2.model_validate(new.json())
        assert [c['toxicity_score'] for c in old.json()['comments']]==[c['toxicity_score'] for c in new.json()['comments']]
        internal_payload=json.loads((ROOT/'contracts/moderation_request.example.json').read_text(encoding='utf-8'))
        internal=with_no_lifespan.post('/api/v1/moderate/comment',json=internal_payload,headers={'Authorization':'Bearer '+token})
        assert internal.status_code==200,internal.status_code
        app.state.predictor=None
        assert with_no_lifespan.post('/api/v2/analyze',json=payload).status_code==503
        app.state.predictor=restored;os.environ['MODEL_PATH']=reg.models['v1']['path']
        assert with_no_lifespan.post('/api/v2/analyze',json=payload).status_code==200
        with_no_lifespan.close()
    finally:
        app.state.predictor=None
        if previous_env is None:os.environ.pop('MODEL_PATH',None)
        else:os.environ['MODEL_PATH']=previous_env
    assert default_model_path()==default_before
    output={'status':'COMPLETE_ACTUAL_CANDIDATE_REVIEW','training_strategy':'frozen_encoder_head_cpu','full_encoder_finetune':False,
      'training_report_sha256':file_hash(candidate_path/'training_report.json'),'threshold':.41,'selection_from_validation_only':True,'test_used_for_selection_or_training':False,
      'historical_ViCTSD_not_fresh_blind':True,'synthetic_development_not_human_gold':True,'metrics':results,'synthetic_development':synthetic,'inference_method':method,
      'gates':gates,'decision':decision,'new_synthetic_advisory_errors':regressions,'production_activation_allowed':False,'production_changed':False,'default_before':default_before,'default_after':default_model_path(),
      'local_registry_candidate_load':candidate_audit,'fallback_injected_fault':fallback,'rollback_to_original_V1':rollback,
      'API_smoke':{'legacy':200,'v2':200,'internal_social_contract':200,'unavailable':503,'rollback_recovered':200,'same_candidate_raw_scores_across_routes':True},
      'input_hashes_unchanged':all(file_hash(Path(item['path']))==item['sha256'] for item in prepared['sources'].values()),
      'elapsed_seconds':round(time.monotonic()-started,2),'limitations':['Head-only CPU experiment; no full encoder/GPU fine-tune.','AI-labelled development results are not real-world evaluation.','No second candidate or rule tuning was performed after opening test labels.','Existing runtime default and policy visibility remain unchanged.']}
    atomic_json(P/'candidate_evaluation.json',output);atomic_json(P/'candidate_event_diagnostics.json',event_counts)
    for name,rows in [('heldout_predictions.csv',predictions),('synthetic_paired.csv',paired)]:
        with (P/name).open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    registry.update(evaluation_status='REVIEW_COMPLETE',review_decision=decision,evaluation_sha256=file_hash(P/'candidate_evaluation.json'),production_default_changed=False)
    atomic_json(registry_path,registry)
    print(json.dumps({'status':output['status'],'gates':gates,'decision':decision,'new_synthetic_advisory_errors':regressions,'default_changed':False,'elapsed_seconds':output['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
