"""Versioned initialization of one bounded follow-up; no training here."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'scripts'))
from prepare_t029_training import prepare
from refine_model import file_hash
from synthetic_data.pipeline import atomic_json
P=Path(__file__).resolve().parent
request='task nào bị từ chối thì sửa task rồi thực hiện tiếp đi'
run_id='T029_genz500_head_cpu_20261103_r04'
config_path=ROOT/'configs/t029_genz500_cpu_head_r04.json'
cfg=json.loads((ROOT/'configs/t029_genz500_cpu_head.json').read_text(encoding='utf-8'))
cfg.update(run_id=run_id,output_dir=str(ROOT/'models/candidates'/run_id),learning_rate=1e-5,synthetic_loss_weight=.1,distillation_weight=1.,
    test_scoring='NOT_RUN: validation-only exploratory follow-up; historical test already inspected in r03',approval_status='RENEWED_USER_REQUEST_BOUNDED_LOCAL_CPU')
if config_path.exists():raise FileExistsError('Never overwrite an existing follow-up')
atomic_json(config_path,cfg)
old=ROOT/'reports/ai_update/all_tasks_cpu_20261103';protocol=old/'evaluation_protocol.json'
refs=json.loads((old/'candidate_evaluation.json').read_text(encoding='utf-8'))['metrics']['ViCTSD_validation']
atomic_json(P/'validation_references.json',{k:v for k,v in refs.items() if k in ('original_V1','existing_default_V1_1')})
base=json.loads((ROOT/'reports/ai_update/T029/genz500_cpu_prepared/manifest.json').read_text(encoding='utf-8'))['base_model_path']
info=prepare(config_path,P/'prepared',base)
atomic_json(P/'cpu_authorization.json',{
    'authorization_type':'bounded_local_cpu_request_v1','authorized_local_task_execution':True,'paid_services_allowed':False,
    'production_activation_allowed':False,'source_user_request':request,'source_user_request_sha256':hashlib.sha256(request.encode('utf-8')).hexdigest(),
    'config_sha256':file_hash(config_path),'prepared_manifest_sha256':file_hash(P/'prepared/manifest.json'),
    'resource':'local_CPU','max_training_seconds':900,'maximum_external_cost':0,'max_cpu_threads':4,
    'user_approved_exact_hyperparameters':False,'max_candidate_runs_this_followup':1,
    'scope_interpretation':'Continued local task rework: one bounded frozen-encoder head-only attempt. Not paid GPU, full fine-tuning or promotion.'})
atomic_json(P/'predeclared_experiment.json',{
    'run_id':run_id,'source_request':request,'config_sha256':file_hash(config_path),
    'prepared_manifest_sha256':file_hash(P/'prepared/manifest.json'),'original_protocol_sha256':file_hash(protocol),
    'validation_references_sha256':file_hash(P/'validation_references.json'),
    'training_implementation_sha256':file_hash(ROOT/'scripts/t029_cpu_head.py'),'review_implementation_sha256':file_hash(ROOT/'scripts/review_t029_validation.py'),
    'rationale':'Reduce synthetic influence .5 to .1 and LR3e-5 to1e-5; increase baseline distillation .5 to1.0. General anti-drift recipe from training/validation behavior, no example-specific rules or label edits.',
    'max_candidate_runs':1,'epochs_max':3,'threads_max':4,'seconds_max':900,'selection':'Historical validation macroF1 at fixed0.41, exploratory reuse disclosed.',
    'test_scoring_allowed':False,'regression_scoring_allowed_this_followup':False,'historical_test_previously_inspected':True,
    'fresh_blind_benchmark_claim_allowed':False,'promotion_allowed':False,'gates_unchanged':True,
    'stop_rule':'One recipe only. If validation fails reject; never relax gates, relabel data or tune on test. A passing screen still needs remaining unchanged release evidence.'})
note='''

## Follow-up r04 — revise refused work and continue

**Follow-up status: IN_PROGRESS.** Prior task DONE and r03 rejection are preserved. One additional bounded CPU head-only research attempt:4threads/900seconds/cost0. New config lowers synthetic loss .5→.1 and LR3e-5→1e-5, increases distillation .5→1.0. Encoder/data/0.41 stay fixed. Historical validation-only selection; no test rescore or example-specific tuning. This exploratory follow-up after the old test was inspected is not fresh independent evaluation. Original quality gates remain frozen; no production promotion.

Evidence: `reports/ai_update/candidate_revision_20261103/predeclared_experiment.json`; current progress in `tasks/AUTO_PROGRESS.md`. Completion requires actual optimizer/reload/integrity evidence and a validation verdict.
'''
names=['tasks/moderation-ai/T029-optional-train-candidate-visobert-on-colab.md','tasks/moderation-ai/T031-optional-model-registry-shadow-and-rollbac.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md','tasks/AUTO_PROGRESS.md']
for name in names:
    with (ROOT/name).open('a',encoding='utf-8') as f:f.write(note)
atomic_json(P/'progress.json',{'status':'IN_PROGRESS','run_id':run_id,'task_files_previous_done':27,
    'followup':'T029/T031 bounded validation-only rework','preflight_tests':'40passed/1warning; initial sandbox temp-write denied, successful elevated rerun',
    'next':'CPU preflight, actual training, validation screen, regression tests, integrity audit','training_performed':False,'test_scored':False,'production_changed':False})
print(json.dumps({'status':'FOLLOWUP_PREPARED','train_rows':info['total_train_rows'],'config':str(config_path),'base_model':base}))
