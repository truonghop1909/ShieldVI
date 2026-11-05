from pathlib import Path
import json,os,sys
ROOT=Path(__file__).resolve().parents[2]
# This script lives in reports/ai_update/autonomous_20261103.
ROOT=Path.cwd();sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0',MODEL_PATH=str(ROOT/'reports/ai_update/autonomous_20261103/no_runtime_checkpoint'))
import torch
torch.set_num_threads(4)
from app.model_registry import LocalModelRegistry
from app.predictor import ViSoBERTPredictor
from app.main import app
from fastapi.testclient import TestClient
from synthetic_data.pipeline import atomic_json
from refine_model import file_hash
registry=LocalModelRegistry(ROOT/'configs/model_registry.local.json')
base=Path(registry.models['v1']['path']);before=file_hash(base/'model.safetensors')
calls=[]
def fail_then_real(path):
    calls.append(path)
    if Path(path).resolve()!=base.resolve():raise RuntimeError('Deliberately injected local primary-load fault')
    return ViSoBERTPredictor(path)
predictor,audit=registry.load('v1_1',shadow=True,loader=fail_then_real)
texts=['Mình góp ý phần màu nền nhé.','Mày là đồ ngu.','Mình xin lỗi vì lời nói trước đó.']
shadow=registry.shadow_compare(predictor,predictor,texts)
with TestClient(app) as client:
    absent=client.get('/health').json();app.state.predictor=predictor
    health=client.get('/health').json()
    payload={'thread_id':'local_smoke_not_dataset','comments':[{'comment_id':str(i),'user_id':'A' if i!=1 else 'B','text':text,'timestamp':f'2026-11-03T10:0{i}:00Z','parent_id':'0' if i else None} for i,text in enumerate(texts)]}
    legacy=client.post('/api/analyze',json=payload);new=client.post('/api/v2/analyze',json=payload)
    assert legacy.status_code==new.status_code==200
    assert [c['toxicity_score'] for c in legacy.json()['comments']]==[c['toxicity_score'] for c in new.json()['comments']]
    assert new.json()['policy_executed'] is False and health['model_loaded']
    app.state.predictor=None
    offline=client.post('/api/v2/analyze',json=payload)
    assert offline.status_code==503
    app.state.predictor=predictor
    recovered=client.post('/api/v2/analyze',json=payload)
    assert recovered.status_code==200
result={'status':'PASS','real_baseline_inference':True,'candidate_available':False,'production_changed':False,'threshold':.41,
    'initial_model_unavailable':not absent['model_loaded'],'healthy_after_local_injection':health['model_loaded'],'fallback':audit,'loader_calls':len(calls),
    'failure_injection':'Deliberate RuntimeError on existing v1_1 primary; actual V1 loaded on fallback. Does not claim real primary failure.',
    'shadow_mechanism':{'same_v1_both_sides':True,'score_equality':shadow['baseline_scores']==shadow['candidate_scores'],'candidate_compared':False},
    'API_legacy_v2_raw_equal':True,'local_unavailable_http':offline.status_code,'local_recovered_http':recovered.status_code,
    'optimizer_steps':0,'base_unchanged':before==file_hash(base/'model.safetensors'),'live_database_accessed':False}
atomic_json(ROOT/'reports/ai_update/autonomous_20261103/local_registry_smoke.json',result)
print(json.dumps(result,ensure_ascii=True))
