"""T029 candidate fine-tune runner. Default is preflight, not training.

Execution requires matching protocol-specific authorization and verified data. Full fine-tuning requires CUDA; the bounded CPU strategy freezes the encoder.
Never edits baseline, source/held-out datasets or the production model selector.
"""
from __future__ import annotations
import argparse,copy,importlib.metadata,json,math,random,time,hashlib
from pathlib import Path
from prepare_t029_training import ROOT,validate_config,resolve
from refine_model import file_hash,metrics
from synthetic_data.pipeline import atomic_json

class TrainingBlocked(RuntimeError):pass

def experimental_scope_matches(scope,cfg,config_sha):
    exp=scope.get('synthetic_experiment',{})
    return (exp.get('authorized') is True and exp.get('run_id')==cfg.get('run_id')
      and exp.get('config_sha256')==config_sha and exp.get('maximum_external_cost')==0
      and exp.get('max_candidate_runs')==1 and cfg.get('data_recipe')=='synthetic_only'
      and cfg.get('evaluation_protocol')=='synthetic_development' and cfg.get('training_strategy')=='frozen_encoder_head_cpu'
      and cfg.get('resource')=='local_CPU' and cfg.get('maximum_external_cost')==0)

def cpu_authorization_matches(cfg,config_sha,prepared_sha,receipt):
    request=receipt.get('source_user_request','')
    return (receipt.get('authorization_type')=='bounded_local_cpu_request_v1'
      and receipt.get('authorized_local_task_execution') is True and receipt.get('paid_services_allowed') is False
      and bool(request.strip()) and receipt.get('source_user_request_sha256')==hashlib.sha256(request.encode('utf-8')).hexdigest()
      and receipt.get('config_sha256')==config_sha and receipt.get('prepared_manifest_sha256')==prepared_sha
      and receipt.get('resource')=='local_CPU' and receipt.get('max_training_seconds')==cfg['max_training_seconds']
      and receipt.get('maximum_external_cost')==0 and receipt.get('max_cpu_threads')==cfg['cpu_threads'])


def checks(config_path,prepared,base_model,approval_path=None,root=ROOT):
    config_path=Path(config_path);prepared=Path(prepared);base_model=Path(base_model)
    cfg=validate_config(json.loads(config_path.read_text(encoding='utf-8')))
    info=json.loads((prepared/'manifest.json').read_text(encoding='utf-8'));blocked=[]
    scope_path=Path(root)/'tasks/CURRENT_AI_SCOPE.json'
    if scope_path.exists():
        scope=json.loads(scope_path.read_text(encoding='utf-8'))
        if scope.get('training_allowed_this_session') is False and not experimental_scope_matches(scope,cfg,file_hash(config_path)):
            blocked.append('Current task scope permits preparation only; new training is not authorized')
    if info['config_sha256']!=file_hash(config_path):blocked.append('Prepared config hash mismatch')
    if file_hash(base_model/'model.safetensors')!=info['base_model_sha256']:blocked.append('Base checkpoint hash mismatch')
    if json.loads((base_model/'threshold_config.json').read_text(encoding='utf-8'))['threshold']!=.41:blocked.append('Threshold mismatch')
    for name,sha in info['output_sha256'].items():
        if file_hash(prepared/name)!=sha:blocked.append('Prepared data changed: '+name)
    for source in info['sources'].values():
        if not Path(source['path']).is_file() or file_hash(source['path'])!=source['sha256']:blocked.append('Input source changed')
    protocol=cfg.get('evaluation_protocol','real_independent')
    if protocol=='synthetic_development':
        from synthetic_data.genz import verified_export
        from prepare_t029_training import remove_near
        from refine_model import clean_train
        try:
            _,threads,_=verified_export(resolve(root,cfg['synthetic_export']))
            dev=[c['text'] for t in threads if t['split']=='development_challenge' for c in t['comments']]
            train=[json.loads(line) for line in (prepared/'train.jsonl').read_text(encoding='utf-8').splitlines()]
            isolated,exact=clean_train(train,dev)
            _,near=remove_near(isolated,dev,cfg['near_duplicate_threshold'],cfg['near_duplicate_min_chars'])
            if exact['overlap_removed'] or near:blocked.append('G2-S: training overlaps development challenge')
            if info.get('evaluation_protocol')!=protocol:blocked.append('G2-S: prepared protocol mismatch')
            if cfg.get('data_recipe')=='synthetic_only':
                from synthetic_data.experiment import verify_prepared
                verify_prepared(cfg,prepared,root)
        except (ValueError,KeyError,OSError):blocked.append('G2-S: synthetic source eligibility failed')
    else:
        # G2 must come from verified real records, not a user-edited READY marker.
        from real_dataset.validation import validate_dataset
        from evaluate_ai_update import evaluate
        real_root=Path(root)/'datasets/real_conversations';real=validate_dataset(real_root)
        manifest_path=resolve(root,cfg['independent_evaluation_manifest'])
        independent=json.loads(manifest_path.read_text(encoding='utf-8'))
        if not real['independent_evaluation_ready'] or not real.get('t028_real_acceptance_ready') or real.get('actual_threads',0)<200 or not independent.get('training_allowed') or not independent.get('data_files'):
            blocked.append('G2: T028 independent real verified evaluation missing')
        else:
            lock=json.loads((real_root/'manifests/evaluation_lock.json').read_text(encoding='utf-8'))
            export_path=real_root/'annotations/evaluation_export.jsonl'
            # Validate rights/solo labels/cohort with dummy predictions solely to check eligibility;
            # no model performance is reported, and the blind labels are not used for selection.
            records=[json.loads(line) for line in export_path.read_text(encoding='utf-8').splitlines()]
            try:evaluate(records,{(row['thread_id'],row['comment_id']):0 for row in records})
            except ValueError:blocked.append('G2: independent record eligibility failed')
            if not independent.get('dataset_lock_sha256')==file_hash(real_root/'manifests/evaluation_lock.json'):blocked.append('G2: evaluation manifest not bound to verified lock')
            from prepare_t029_training import remove_near
            from refine_model import clean_train
            train=[json.loads(line) for line in (prepared/'train.jsonl').read_text(encoding='utf-8').splitlines()]
            isolated,exact=clean_train(train,[row['raw_text'] for row in records])
            _,near=remove_near(isolated,[row['raw_text'] for row in records],cfg['near_duplicate_threshold'],cfg['near_duplicate_min_chars'])
            if exact['overlap_removed'] or near:blocked.append('G2: prepared training overlaps locked independent evaluation')
    receipt=json.loads(Path(approval_path).read_text(encoding='utf-8')) if approval_path and Path(approval_path).exists() else {}
    cpu=cfg.get('training_strategy')=='frozen_encoder_head_cpu'
    if cpu:
        if not cpu_authorization_matches(cfg,file_hash(config_path),file_hash(prepared/'manifest.json'),receipt):
            blocked.append('G3-CPU: bounded local request authorization missing or mismatched')
        if not Path(cfg['output_dir']).resolve().is_relative_to((Path(root)/'models/candidates').resolve()):blocked.append('CPU candidate must stay in repository models/candidates')
    else:
        if not (receipt.get('approved') is True and receipt.get('config_sha256')==file_hash(config_path)
          and receipt.get('prepared_manifest_sha256')==file_hash(prepared/'manifest.json') and receipt.get('resource')==cfg['resource']
          and receipt.get('max_training_seconds')==cfg['max_training_seconds'] and receipt.get('cost_acknowledged') is True):
            blocked.append('G3: exact config/data/resource approval receipt missing')
    versions={}
    for package,expected in cfg['required_versions'].items():
        try:versions[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:versions[package]=None
        if versions[package]!=expected:blocked.append('Version mismatch: '+package)
    import torch
    if not cpu and not torch.cuda.is_available():blocked.append('CUDA GPU unavailable; CPU training is disabled for full fine-tuning')
    output=Path(cfg['output_dir']).resolve();base=base_model.resolve()
    if output==base or output.is_relative_to(base) or base.is_relative_to(output):blocked.append('Candidate output overlaps baseline')
    if output.exists():blocked.append('Candidate output already exists; choose a new run ID')
    return {'status':'BLOCKED' if blocked else 'READY_TO_RUN','blockers':blocked,'versions':versions,'training_performed':False},cfg,info

def run(config_path,prepared,base_model,approval_path=None,execute=False,root=ROOT):
    report,cfg,info=checks(config_path,prepared,base_model,approval_path,root)
    if not execute:return report
    if report['blockers']:raise TrainingBlocked('; '.join(report['blockers']))
    if cfg.get('training_strategy')=='frozen_encoder_head_cpu':
        from t029_cpu_head import train
        return train(cfg,prepared,base_model,report)
    import torch
    from transformers import AutoModelForSequenceClassification,AutoTokenizer
    from torch.utils.data import DataLoader
    from torch.nn import functional as F
    started=time.monotonic();output=Path(cfg['output_dir']);output.mkdir(parents=True,exist_ok=False)
    seed=cfg['seed'];random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
    tokenizer=AutoTokenizer.from_pretrained(str(base_model),local_files_only=True)
    model=AutoModelForSequenceClassification.from_pretrained(str(base_model),local_files_only=True).to('cuda')
    for parameter in model.parameters():parameter.requires_grad=True
    train=[json.loads(line) for line in (Path(prepared)/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    validation=[json.loads(line) for line in (Path(prepared)/'validation.jsonl').read_text(encoding='utf-8').splitlines()]
    def collate(rows):
        tokens=tokenizer([row['text'] for row in rows],padding=True,truncation=True,max_length=cfg['max_length'],return_tensors='pt')
        return {key:value.to('cuda') for key,value in tokens.items()},torch.tensor([row['label'] for row in rows],device='cuda'),torch.tensor([row.get('sample_weight',1.0) for row in rows],device='cuda')
    loader=DataLoader(train,batch_size=cfg['batch_size'],shuffle=True,collate_fn=collate,num_workers=0)
    def validate_model():
        model.eval();labels=[];probabilities=[]
        with torch.inference_mode():
            for start in range(0,len(validation),cfg['batch_size']):
                rows=validation[start:start+cfg['batch_size']];tokens,y,_=collate(rows)
                probabilities.extend(model(**tokens).logits.softmax(-1)[:,1].tolist());labels.extend(y.tolist())
        return metrics(labels,probabilities,.41)
    result={'status':'RUNNING','training_performed':False,'config':cfg,'prepared_manifest_sha256':file_hash(Path(prepared)/'manifest.json'),
      'base_sha256_before':file_hash(Path(base_model)/'model.safetensors'),'threshold':.41,'test_scored':False,'epochs':[],'optimizer_steps':0,'activated':False}
    atomic_json(output/'training_report.json',result)
    optimizer=torch.optim.AdamW(model.parameters(),lr=cfg['learning_rate'],weight_decay=cfg['weight_decay'])
    try:
        result['baseline_validation']=validate_model();best=None;best_state=None;wait=0
        for epoch in range(1,cfg['epochs']+1):
            model.train();optimizer.zero_grad(set_to_none=True);loss_sum=0.;accum=cfg['gradient_accumulation_steps']
            for index,(tokens,y,weight) in enumerate(loader):
                if time.monotonic()-started>cfg['max_training_seconds']:raise TimeoutError('Approved training time budget exceeded')
                groupsize=min(accum,len(loader)-(index//accum)*accum)
                losses=F.cross_entropy(model(**tokens).logits,y,reduction='none');loss=(losses*weight).sum()/weight.sum()
                (loss/groupsize).backward();loss_sum+=float(loss.detach())
                if (index+1)%accum==0 or index+1==len(loader):
                    torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step();optimizer.zero_grad(set_to_none=True)
                    result['optimizer_steps']+=1;result['training_performed']=True
            score=validate_model();result['epochs'].append({'epoch':epoch,'validation':score,'loss_sum':loss_sum})
            if best is None or score['macro_f1']>best['validation']['macro_f1']:
                best={'epoch':epoch,'validation':score};best_state={key:value.detach().cpu().clone() for key,value in model.state_dict().items()};wait=0
            else:wait+=1
            atomic_json(output/'training_report.json',result)
            if wait>=cfg['early_stopping_patience']:break
        model.load_state_dict(best_state);model.eval();model.save_pretrained(str(output),safe_serialization=True);tokenizer.save_pretrained(str(output))
        atomic_json(output/'threshold_config.json',{'threshold':.41,'approval_status':'candidate_not_deployed','selected_on':'validation_only'})
        probe=tokenizer([validation[0]['text']],return_tensors='pt',truncation=True,max_length=cfg['max_length']).to('cuda')
        with torch.inference_mode():expected=model(**probe).logits.softmax(-1)[:,1].cpu()
        del model;torch.cuda.empty_cache()
        reloaded=AutoModelForSequenceClassification.from_pretrained(str(output),local_files_only=True).to('cuda').eval()
        with torch.inference_mode():actual=reloaded(**probe).logits.softmax(-1)[:,1].cpu()
        if not torch.allclose(expected,actual,atol=1e-5,rtol=1e-5):raise RuntimeError('Candidate reload prediction mismatch')
        result.update(status='CANDIDATE_SAVED_NOT_DEPLOYED',selected=best,reload_smoke_pass=True,elapsed_seconds=round(time.monotonic()-started,2),candidate_sha256=file_hash(output/'model.safetensors'))
    except Exception as exc:
        result.update(status='FAILED_NOT_DEPLOYED',error_type=type(exc).__name__,elapsed_seconds=round(time.monotonic()-started,2));raise
    finally:
        result['base_sha256_after']=file_hash(Path(base_model)/'model.safetensors')
        result['baseline_unchanged']=result['base_sha256_before']==result['base_sha256_after']
        result['heldouts_unchanged']=all(file_hash(item['path'])==item['sha256'] for item in info['sources'].values())
        atomic_json(output/'training_report.json',result)
        if not result['baseline_unchanged'] or not result['heldouts_unchanged']:raise RuntimeError('Protected source checksum changed')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=ROOT/'configs/t029_candidate.json');p.add_argument('--prepared',type=Path,default=ROOT/'reports/ai_update/T029/prepared');p.add_argument('--base-model',type=Path,required=True);p.add_argument('--approval',type=Path);p.add_argument('--run',action='store_true');p.add_argument('--report',type=Path,default=ROOT/'reports/ai_update/T029/preflight.json');a=p.parse_args()
    result=run(a.config,a.prepared,a.base_model,a.approval,execute=a.run);atomic_json(a.report,result);print(json.dumps(result,ensure_ascii=True));raise SystemExit(2 if result['status']=='BLOCKED' else 0)
if __name__=='__main__':main()
