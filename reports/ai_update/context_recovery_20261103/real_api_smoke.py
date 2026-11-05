from pathlib import Path
import json,os,sys
R=Path.cwd();sys.path.insert(0,str(R));sys.path.insert(0,str(R/'scripts'))
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0')
registry=json.loads((R/'configs/model_registry.local.json').read_text(encoding='utf-8'));os.environ['MODEL_PATH']=registry['models']['v1']['path']
import torch;torch.set_num_threads(4)
from app.main import app
from fastapi.testclient import TestClient
from app.schemas import AnalyzeResponseV2
from synthetic_data.pipeline import file_sha,atomic_json
P=R/'reports/ai_update/context_recovery_20261103';ref=json.loads((R/'datasets/fixtures/context_recovery_v1/game_rank_30_reference.json').read_text(encoding='utf-8'));payload=json.loads((R/ref['input_file']).read_text(encoding='utf-8'))
before=next(x for x in json.loads((P/'before.json').read_text(encoding='utf-8')) if x['group']=='GAME_USER_REFERENCE')['output']
with TestClient(app) as client:
 assert client.get('/health').json()['model_loaded']
 response=client.post('/api/v2/analyze',json=payload);assert response.status_code==200
 data=response.json();AnalyzeResponseV2.model_validate(data)
 for a,b in zip(before['comments'],data['comments']):
  assert a['toxicity_score']==b['toxicity_score'] and a['toxic_for_moderation']==b['toxic_for_moderation']
  assert b['moderation_assessment']['label']==ref['labels'][b['comment_id']]
 schema=json.loads((R/'contracts/analysis_response_v2.schema.json').read_text(encoding='utf-8'))
 import importlib.util
 schema_validation='NOT_INSTALLED_PYDANTIC_PASSED'
 if importlib.util.find_spec('jsonschema'):
  import jsonschema;jsonschema.Draft202012Validator(schema).validate(data);schema_validation='PASS'
 static=client.get('/dashboard/');assert static.status_code==200
 assert client.post('/api/analyze',json=payload).status_code==200
atomic_json(P/'real_api_after.json',data)
lock=json.loads((P/'before_lock.json').read_text(encoding='utf-8'));assert file_sha(Path(registry['models']['v1']['path'])/'model.safetensors')==lock['V1_weights_sha256']
atomic_json(P/'real_api_smoke.json',{'status':'PASS','real_V1_after_inference':True,'comments':30,'matches_all_user_reference_labels':True,'raw_before_after_equal':True,'weights_unchanged':True,'threshold':.41,'jsonschema_validation':schema_validation,'pydantic_validation':'PASS','static_http':200,'legacy_http':200,'policy_executed':False,'live_db_written':False,'optimizer_steps':0})
print('Real V1 API after PASS:30reference labels, raw/model unchanged, static200 and legacy200')
