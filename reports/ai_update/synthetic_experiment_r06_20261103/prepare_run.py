"""Explicit one-run free CPU authorization; preserve real-world task blockers."""
import hashlib,json,shutil,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
from synthetic_data.experiment import export_dataset
from prepare_t029_training import prepare
from train_t029_candidate import run
request_path=Path('C:/Users/admin/.codex/attachments/44a6f494-fb56-43cf-96c5-f4858b199a7a/Pasted text.txt')
request=request_path.read_text(encoding='utf-8');run_id='T029_synthetic_only_head_cpu_20261103_r06'
config_path=R/'configs/t029_synthetic_only_cpu_r06.json'
if config_path.exists() or (P/'progress.json').exists():raise FileExistsError('Run already prepared; use saved progress instead of recreating authorization')
shutil.copy2(request_path,P/'source_request.txt')
cfg=json.loads((R/'configs/t029_genz500_cpu_head_r04.json').read_text(encoding='utf-8'))
cfg.update(run_id=run_id,output_dir=str(R/'models/candidates'/run_id),data_recipe='synthetic_only',
 original_train=None,experimental_dataset='datasets/synthetic_genz',validation='datasets/synthetic_genz/validation_comments.csv',test_text_only=None,
 max_synthetic_fraction=1.,synthetic_loss_weight=1.,learning_rate=1e-5,distillation_weight=.25,
 class_weight_policy='sqrt(clean/toxic), capped4',approval_status='EXPLICIT_EXPERIMENTAL_FREE_CPU_AUTHORIZATION',
 selection_metric='synthetic_validation_macro_f1_at_0.41',
 test_scoring='Synthetic challenge scored once after selection; already-viewed development, not independent evaluation',
 experiment_status='EXPERIMENTAL_NOT_PRODUCTION',estimated_cost='LocalCPU only, max4threads/900seconds, one run; externalcost0')
atomic_json(config_path,cfg)
scope_path=R/'tasks/CURRENT_AI_SCOPE.json';scope=json.loads(scope_path.read_text(encoding='utf-8'))
scope['synthetic_experiment']={'authorized':True,'status':'IN_PROGRESS','run_id':run_id,'config_sha256':file_sha(config_path),
 'request_sha256':file_sha(request_path),'max_candidate_runs':1,'maximum_external_cost':0,'resource':'local_CPU',
 'original_T028_real_status':'BLOCKED','original_T029_real_acceptance_unchanged':True,'production_activation_allowed':False}
atomic_json(scope_path,scope)
note='\n\n## CURRENT explicit synthetic experiment r06 — IN_PROGRESS\n\nLatest attached request authorizes actual free-resource synthetic training separately from blocked real T028/T029 acceptance. Reuse canonical500 without changing original text/AI labels/splits; derive a three-way family view, no real training due unreverified local-copy rights. One new CPU frozen-encoder/full-classifier-head candidate, max4threads/900s/cost0. Different from r05: synthetic-only, class balancing, synthetic validation early stopping, originalV1 base. Real/general training remains disabled; exact r06 config/receipt is the only local exception. Evidence reports/ai_update/synthetic_experiment_r06_20261103/.\n'
for name in ('tasks/AUTO_PROGRESS.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md'):
    with (R/name).open('a',encoding='utf-8') as f:f.write(note)
with (R/'AGENTS.md').open('a',encoding='utf-8') as f:
    f.write('\n- Latest attached synthetic-experiment request authorizes one hash-bound r06synthetic-only CPUhead experiment(max4threads/900s/cost0), separately from blocked real acceptance. Reuse500/AI labels, no paid API/GPU, no production switch. Current scope exception must match exact config/receipt; real T028 and formal T029/T030 gates remain unmet.\n')
atomic_json(P/'progress.json',{'status':'DATASET_IN_PROGRESS','run_id':run_id,'training_performed':False,'T028_real':'BLOCKED','next':'Pilot20 audit then validated reuse batches to500'})
def checkpoint(end,batch):
    atomic_json(P/'progress.json',{'status':'DATASET_IN_PROGRESS','run_id':run_id,'completed_threads':end,'last_batch':batch['threads'],
      'source_reused':True,'new_utterances_generated':0,'training_performed':False,'next':'Continue validated reuse batches'})
    with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:f.write(f'\nr06dataset checkpoint:{end}/500threads exported, lastbatch{batch["threads"]}, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.\n')
dataset=export_dataset(R/'datasets/synthetic_genz',progress=checkpoint)
base=Path(json.loads((R/'reports/ai_update/T029/genz500_cpu_prepared/manifest.json').read_text(encoding='utf-8'))['base_model_path'])
info=prepare(config_path,P/'prepared',base)
atomic_json(P/'cpu_authorization.json',{'authorization_type':'bounded_local_cpu_request_v1','authorized_local_task_execution':True,
 'source_user_request':request,'source_user_request_sha256':hashlib.sha256(request.encode()).hexdigest(),'source_attachment_sha256':file_sha(request_path),
 'config_sha256':file_sha(config_path),'prepared_manifest_sha256':file_sha(P/'prepared/manifest.json'),
 'resource':'local_CPU','max_training_seconds':900,'maximum_external_cost':0,'max_cpu_threads':4,
 'paid_services_allowed':False,'production_activation_allowed':False,'user_approved_exact_hyperparameters':False,'max_candidate_runs':1,
 'scope':'Explicit synthetic experimental branch only. Not approval for real-world acceptance, GPU, external upload or production.'})
atomic_json(P/'predeclared_protocol.json',{'run_id':run_id,'config_sha256':file_sha(config_path),'dataset_manifest_sha256':file_sha(R/'datasets/synthetic_genz/dataset_manifest.json'),
 'split_manifest_sha256':file_sha(R/'datasets/synthetic_genz/split_manifest.json'),'prepared_manifest_sha256':file_sha(P/'prepared/manifest.json'),
 'training_implementation_sha256':file_sha(R/'scripts/t029_cpu_head.py'),'baseline_path':str(base),'baseline_sha256':file_sha(base/'model.safetensors'),
 'r05_path':str(R/'models/candidates/T029_genz500_head_cpu_20261103_r05'),
 'selection':'Best synthetic-validation macroF1 only; no model selection on challenge. Historical ViCTSD test not read or scored.',
 'max_candidate_runs':1,'challenge_scored_after_selection_only':True,'new_real_training_used':False,
 'independent_evaluation':False,'r05_model_training_overlap_with_holdouts_must_be_checked':True,
 'promotion_allowed':False,'T028_real':'BLOCKED','formal_T029_T030_real_acceptance':'BLOCKED'})
preflight=run(config_path,P/'prepared',base,P/'cpu_authorization.json',execute=False);atomic_json(P/'preflight.json',preflight)
atomic_json(P/'progress.json',{'status':'READY_TO_TRAIN' if preflight['status']=='READY_TO_RUN' else 'BLOCKED','run_id':run_id,
 'dataset_threads':dataset['threads'],'dataset_comments':dataset['comments'],'splits':dataset['splits'],
 'training_rows':info['total_train_rows'],'validation_rows':info['validation_rows'],'training_performed':False,
 'next':'Run related checks, then exactly one authorized CPU experiment','blockers':preflight['blockers']})
print(json.dumps({'preflight':preflight['status'],'threads':dataset['threads'],'comments':dataset['comments'],'labels':dataset['labels'],
 'splits':dataset['splits'],'training_rows':info['total_train_rows'],'validation_rows':info['validation_rows'],'positive_weight':info['positive_sample_weight'],'blockers':preflight['blockers']}))
