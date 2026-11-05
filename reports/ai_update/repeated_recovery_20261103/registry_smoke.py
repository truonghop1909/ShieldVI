"""Actual r06 local shadow/fallback/rollback; no default or running-service change."""
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
registry=json.loads((R/'configs/model_registry.independent_readiness.local.json').read_text(encoding='utf-8'))
model=R/'models/candidates/T029_synthetic_only_head_cpu_20261103_r06'
entry=copy.deepcopy(registry['models']['candidate_r05']);entry.update(path=str(model),approved_for_selection=False,role='experimental')
entry['sha256']={name:file_sha(model/name) for name in entry['sha256'] if (model/name).is_file()}
registry['models']['candidate_r06']=entry
registry.update(candidate_run_id=model.name,mode='explicit_local_shadow_only',production_default_changed=False,
    evaluation_status='SYNTHETIC_ONLY_NOT_INDEPENDENT',review_decision='KEEP_EXISTING_DEFAULT_NO_PROMOTION',
    training_report_sha256=file_sha(model/'training_report.json'),evaluation_sha256=file_sha(P/'evaluation/evaluation.json'),
    rule_sha256={name:file_sha(R/'services/moderation-ai/app'/name) for name in ('context_signals.py','target_signals.py','signal_engine.py')})
path=R/'configs/model_registry.repeated_recovery.local.json'
if path.exists():raise FileExistsError('Keep prior registry evidence')
atomic_json(path,registry);reg=LocalModelRegistry(path);before=default_model_path()
try:reg.load('candidate_r06')
except RegistryError:implicit_refused=True
else:raise AssertionError('Implicit activation unexpectedly allowed')
candidate,chosen=reg.load('candidate_r06',shadow=True)
def fail_candidate(path):
    if Path(path).resolve()==model.resolve():raise RuntimeError('Injected local loader failure')
    return ViSoBERTPredictor(path)
fallback,failure=reg.load('candidate_r06',shadow=True,loader=fail_candidate)
assert failure['fallback_used'] and failure['selected']=='v1'
shadow=reg.shadow_compare(fallback,candidate,['Xin chào các thành viên mới.','Buổi họp diễn ra vào chiều mai.'])
payload={'thread_id':'ISOLATED_R06_ROLLBACK','comments':[
    {'comment_id':'a','user_id':'Alice','timestamp':'2026-11-03T01:00:00Z','text':'Bản thuyết trình của mình đây.'},
    {'comment_id':'b','user_id':'Bob','parent_id':'a','timestamp':'2026-11-03T01:01:00Z','text':'Mày ngu thật khi viết bản này.'},
    {'comment_id':'c','user_id':'Chau','parent_id':'b','timestamp':'2026-11-03T01:02:00Z','text':'Đừng gọi bạn ấy ngu.'},
    {'comment_id':'d','user_id':'Bob','parent_id':'a','timestamp':'2026-11-03T01:03:00Z','text':'Bạn vô dụng trong nhóm.'},
    {'comment_id':'e','user_id':'Bob','parent_id':'a','timestamp':'2026-11-03T01:04:00Z','text':'Mình xin lỗi vì đã gọi bạn ngu.'}]}
saved=(getattr(app.state,'predictor',None),getattr(app.state,'error',None))
try:
    client=TestClient(app);app.state.predictor=candidate;app.state.error=None
    initial=client.post('/api/v2/analyze',json=payload);assert initial.status_code==200
    assert initial.json()['evidence'][0]['evidence_comment_ids']==['b','d']
    app.state.predictor=None;unavailable=client.post('/api/v2/analyze',json=payload);assert unavailable.status_code==503
    app.state.predictor=fallback;recovered=client.post('/api/v2/analyze',json=payload);assert recovered.status_code==200
    assert recovered.json()['evidence'][0]['evidence_comment_ids']==['b','d']
finally:app.state.predictor=saved[0];app.state.error=saved[1]
assert before==default_model_path() and candidate.threshold==fallback.threshold==.41
atomic_json(P/'registry_smoke.json',{'status':'PASS','actual_local_models_loaded':True,'implicit_candidate_refused':implicit_refused,
    'shadow':chosen,'fallback':failure,'scores_mechanics_only':shadow,'candidate_API':initial.status_code,'unavailable':unavailable.status_code,
    'rollback_API':recovered.status_code,'evidence_before_and_after_rollback':['b','d'],'excluded_non_attacks':['c','e'],
    'default_before':before,'default_after':default_model_path(),'production_changed':False,'training_performed':False,
    'limitations':'Isolated ASGI/new-process mechanics; no running demo reconfigured, no real-world quality/release approval.'})
print(json.dumps({'status':'PASS','shadow_actual_r06':True,'rollback':'200->503->200','default_changed':False}))
