"""One explicitly requested offline continuation; reuse the verified T029 runner."""
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from prepare_t029_training import prepare,validate_config
from train_t029_candidate import run
from refine_model import file_hash
from review_t029_validation import validation_gates
from synthetic_data.pipeline import atomic_json

P=Path(__file__).resolve().parent
REQUEST='hãy nạp dataset mới để train mô hình đi'
RUN_ID='T029_genz500_head_cpu_20261103_r05'
config_path=ROOT/'configs/t029_genz500_cpu_head_r05.json'
base=ROOT/'models/visobert_head_refined'
model=ROOT/'models/candidates'/RUN_ID
prepared=P/'prepared'
tracking=['tasks/AUTO_PROGRESS.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md',
          'tasks/moderation-ai/T029-optional-train-candidate-visobert-on-colab.md']

def append(note):
    for name in tracking:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(note)

def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))

if config_path.exists() or model.exists() or (P/'progress.json').exists():
    raise FileExistsError('Never overwrite an existing training run; use a new declared run ID')
cfg=load(ROOT/'configs/t029_genz500_cpu_head_r04.json')
cfg.update(run_id=RUN_ID,base_model='models/visobert_head_refined',original_v1=False,
    base_reference_id='existing_default_V1_1',output_dir=str(model),learning_rate=5e-6,
    synthetic_loss_weight=.1,distillation_weight=1.,approval_status='EXPLICIT_USER_REQUEST_TO_TRAIN_NEW_DATASET',
    test_scoring='NOT_RUN: exploratory continuation selected on historical validation only; test already viewed previously')
validate_config(cfg);atomic_json(config_path,cfg)
atomic_json(P/'progress.json',{'status':'PREPARING','request':REQUEST,'run_id':RUN_ID,'training_performed':False,
    'base':'approved V1.1; same frozen encoder as V1','max_threads':4,'max_seconds':900,'external_cost':0,
    'test_scored':False,'default_changed':False,'next':'Verify sources and prepare augmentation'})
append(f'''\n\n## CURRENT requested training r05 — IN_PROGRESS\n\nUser explicitly asks to load new dataset and train: “{REQUEST}”. One bounded local CPU classifier-head continuation from approved V1.1, encoder frozen; max4threads/900s/cost0. DatasetGenZ500 train split +ViCTSD original; keep development/test/labels/default unchanged. Newrun {RUN_ID}; evidence reports/ai_update/train_genz500_r05_20261103/. Previous DONE states and r03/r04 negative decisions are preserved. No GPU/full-encoder training or promotion.\n''')
try:
    info=prepare(config_path,prepared,base)
    atomic_json(P/'cpu_authorization.json',{
      'authorization_type':'bounded_local_cpu_request_v1','authorized_local_task_execution':True,
      'source_user_request':REQUEST,'source_user_request_sha256':hashlib.sha256(REQUEST.encode('utf-8')).hexdigest(),
      'config_sha256':file_hash(config_path),'prepared_manifest_sha256':file_hash(prepared/'manifest.json'),
      'resource':'local_CPU','max_training_seconds':900,'maximum_external_cost':0,'max_cpu_threads':4,
      'paid_services_allowed':False,'production_activation_allowed':False,'user_approved_exact_hyperparameters':False,
      'scope':'Explicit train request; one local frozen-encoder head-only continuation. No GPU cost or active checkpoint replacement.'})
    old=ROOT/'reports/ai_update/all_tasks_cpu_20261103'
    refs=load(old/'candidate_evaluation.json')['metrics']['ViCTSD_validation']
    refs={key:value for key,value in refs.items() if key in ('original_V1','existing_default_V1_1')}
    atomic_json(P/'validation_references.json',refs)
    protocol=old/'evaluation_protocol.json'
    atomic_json(P/'predeclared_experiment.json',{
      'request':REQUEST,'run_id':RUN_ID,'base_reference_id':'existing_default_V1_1',
      'base_sha256':file_hash(base/'model.safetensors'),'config_sha256':file_hash(config_path),
      'prepared_manifest_sha256':file_hash(prepared/'manifest.json'),'original_protocol_sha256':file_hash(protocol),
      'validation_references_sha256':file_hash(P/'validation_references.json'),
      'training_code_sha256':file_hash(ROOT/'scripts/t029_cpu_head.py'),
      'validation_code_sha256':file_hash(ROOT/'scripts/review_t029_validation.py'),
      'recipe':'Start from current approved V1.1 head, LR5e-6, synthetic weight.1, distillation1.0, seed20261103, max3epochs/patience1. All data and0.41 fixed.',
      'selection':'Validation macroF1 only; one exploratory run. Prior historical test already inspected, not fresh blind evidence.',
      'max_candidate_runs':1,'max_seconds':900,'max_threads':4,'maximum_external_cost':0,
      'test_scoring_allowed':False,'development_challenge_scoring_allowed':False,'promotion_allowed':False})
    preflight=run(config_path,prepared,base,P/'cpu_authorization.json',execute=False)
    atomic_json(P/'preflight.json',preflight)
    if preflight['status']!='READY_TO_RUN':raise RuntimeError('Preflight failed: '+str(preflight['blockers']))
    atomic_json(P/'progress.json',{'status':'TRAINING','run_id':RUN_ID,'training_performed':False,
      'training_rows':info['total_train_rows'],'synthetic_rows':info['synthetic_train_rows'],
      'test_scored':False,'default_changed':False,'next':'Actual bounded optimizer then reload/validation review'})
    result=run(config_path,prepared,base,P/'cpu_authorization.json',execute=True)
    atomic_json(P/'training_execution.json',result)
    reference=refs['existing_default_V1_1']
    for key,value in reference.items():
        actual=result['baseline_validation'][key]
        assert math.isclose(actual,value,rel_tol=0,abs_tol=1e-6) if isinstance(value,float) else actual==value
    gates=validation_gates(result['candidate_validation'],refs,load(protocol)['original_validation_gate'])
    passed=all(all(values.values()) for values in gates.values())
    decision='PASS_VALIDATION_SCREEN_ONLY' if passed else 'REJECT_PROMOTION_KEEP_EXISTING_DEFAULT'
    atomic_json(P/'validation_review.json',{'status':'VALIDATION_SCREEN_COMPLETE','decision':decision,
      'base_reference_id':'existing_default_V1_1','baseline_validation':result['baseline_validation'],
      'candidate_validation':result['candidate_validation'],'gates':gates,'reference_validation':refs,
      'original_protocol_sha256':file_hash(protocol),'training_report_sha256':file_hash(model/'training_report.json'),
      'candidate_sha256':file_hash(model/'model.safetensors'),'threshold':.41,'promotion_allowed':False,
      'test_scored':False,'development_challenge_scored':False,'production_changed':False,
      'limitation':'Historical validation reused for exploratory model selection; no new blind performance claim. No r05 regression or API inference claimed.'})
    atomic_json(P/'progress.json',{'status':'TRAINED_PENDING_FINAL_CHECKS','run_id':RUN_ID,'training_performed':True,
      'optimizer_steps':result['optimizer_steps'],'training_seconds':result['elapsed_seconds'],'decision':decision,
      'test_scored':False,'default_changed':False,'next':'Run related regression and protected-source integrity checks; update task/report'})
    print(json.dumps({'status':'TRAINED_PENDING_FINAL_CHECKS','decision':decision,'steps':result['optimizer_steps'],
      'seconds':result['elapsed_seconds'],'validation_macro_f1':result['candidate_validation']['macro_f1']}),flush=True)
except BaseException as exc:
    atomic_json(P/'progress.json',{'status':'FAILED_NOT_ACTIVATED','run_id':RUN_ID,'error_type':type(exc).__name__,
      'error':str(exc),'default_changed':False,'next':'Inspect training log/report; do not restart or overwrite this run'})
    append(f'\n\nCurrent r05 execution stopped: {type(exc).__name__}: {exc}. Follow-up is not DONE; preserve logs/checkpoint and inspect before another run.\n')
    raise
