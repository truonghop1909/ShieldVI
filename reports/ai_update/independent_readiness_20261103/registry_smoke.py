"""Real local shadow/fallback/rollback mechanics, not model promotion or accuracy."""
import copy,json,os,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0',OMP_NUM_THREADS='4',MKL_NUM_THREADS='4')
sys.path.insert(0,str(R/'services/moderation-ai'));sys.path.insert(0,str(R/'scripts'))
import torch
torch.set_num_threads(4)
from app.model_registry import LocalModelRegistry,RegistryError
from app.predictor import ViSoBERTPredictor,default_model_path
from app.main import app
from fastapi.testclient import TestClient
from synthetic_data.pipeline import atomic_json,file_sha
source=R/'configs/model_registry.cpu_r03.local.json';registry=json.loads(source.read_text(encoding='utf-8'))
cfg=json.loads((R/'configs/t029_genz500_cpu_head_r05.json').read_text(encoding='utf-8'));model=Path(cfg['output_dir'])
entry=copy.deepcopy(registry['models']['candidate_cpu']);entry.update(path=str(model),approved_for_selection=False)
entry['sha256']={name:file_sha(model/name) for name in entry['sha256'] if (model/name).is_file()}
registry['models']['candidate_r05']=entry
registry.update(mode='explicit_local_shadow_only',candidate_run_id=cfg['run_id'],evaluation_status='LOCAL_MECHANICS_ONLY_NO_NEW_QUALITY_APPROVAL',
  review_decision='KEEP_EXISTING_DEFAULT_R05_PROMOTION_REJECTED',training_report_sha256=file_sha(model/'training_report.json'),
  evaluation_sha256=file_sha(R/'reports/ai_update/train_genz500_r05_20261103/validation_review.json'),
  rule_sha256={name:file_sha(R/name) for name in ['services/moderation-ai/app/context_signals.py','services/moderation-ai/app/target_signals.py','services/moderation-ai/app/signal_engine.py']})
path=R/'configs/model_registry.independent_readiness.local.json';atomic_json(path,registry)
reg=LocalModelRegistry(path);before=default_model_path()
try:reg.load('candidate_r05')
except RegistryError:implicit_refused=True
else:raise AssertionError('Candidate unexpectedly allowed implicit activation')
candidate,chosen=reg.load('candidate_r05',shadow=True)
def fail_candidate(path):
    if Path(path).resolve()==model.resolve():raise RuntimeError('Deliberate local candidate-loader failure')
    return ViSoBERTPredictor(path)
fallback,failure=reg.load('candidate_r05',shadow=True,loader=fail_candidate)
assert failure['fallback_used'] and failure['selected']=='v1'
scores=reg.shadow_compare(fallback,candidate,['Xin chào mọi người.','Mình đang chuẩn bị bài thuyết trình.'])
assert len(scores['candidate_scores'])==2
payload={'thread_id':'LOCAL_REGISTRY_MECHANICS','comments':[{'comment_id':'a','user_id':'A','timestamp':'2026-01-01T00:00:00Z','text':'Xin chào mọi người.'}]}
saved_predictor=getattr(app.state,'predictor',None);saved_error=getattr(app.state,'error',None)
try:
    client=TestClient(app);app.state.predictor=candidate;app.state.error=None
    initial=client.post('/api/v2/analyze',json=payload);assert initial.status_code==200
    app.state.predictor=None;unavailable=client.post('/api/v2/analyze',json=payload);assert unavailable.status_code==503
    app.state.predictor=fallback;recovered=client.post('/api/v2/analyze',json=payload);assert recovered.status_code==200
finally:app.state.predictor=saved_predictor;app.state.error=saved_error
assert before==default_model_path() and candidate.threshold==fallback.threshold==.41
atomic_json(P/'registry_smoke.json',{'status':'PASS','actual_local_models_loaded':True,'implicit_candidate_refused':implicit_refused,
 'shadow':chosen,'fallback':failure,'scores_are_mechanics_only':scores,'candidate_API':initial.status_code,'unavailable':unavailable.status_code,'rollback_API':recovered.status_code,
 'default_before':before,'default_after':default_model_path(),'production_changed':False,'training_performed':False,
 'limitations':'Actual new-process local ASGI mechanics only; does not change running demo or approve model quality.'})
print(json.dumps({'status':'PASS','actual_model_shadow':True,'fallback_original_V1':True,'rollback':'200->503->200','default_changed':False}))
