"""T020 baseline only: offline inference, contract snapshots and tests; no training."""
import csv,gc,hashlib,importlib,importlib.metadata as metadata,json,os,secrets,subprocess,sys,time,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path
R=Path(__file__).resolve().parents[4]
O=Path(__file__).resolve().parent
SERVICE=R/'services/moderation-ai'
V1=Path(r'C:\Users\admin\Downloads\visobert_toxic_final')
os.environ.update({'PYTHONDONTWRITEBYTECODE':'1','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','STORE_SUMMARIES':'0','DB_PATH':str(O/'isolated_unused_summaries.sqlite3'),'REVIEW_DB_PATH':str(O/'isolated_unused_reviews.sqlite3')})
sys.dont_write_bytecode=True
sys.path.insert(0,str(R))
def now():return datetime.now(timezone(timedelta(hours=7))).isoformat()
def dump(name,value):
 p=O/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def snapshot(paths):return {str(p.resolve()):{'sha256':sha(p),'size':p.stat().st_size} for p in sorted(set(paths)) if p.is_file()}
def command(args,cwd,log):
 started=time.monotonic();result=subprocess.run(args,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace')
 (O/log).write_text(result.stdout+result.stderr,encoding='utf-8')
 return {'command':args,'cwd':str(cwd),'exit_code':result.returncode,'elapsed_seconds':round(time.monotonic()-started,3),'log':log,'summary':result.stdout.strip().splitlines()[-1] if result.stdout.strip() else result.stderr.strip()[-300:]}
started=time.monotonic()
print('T020 inventory',flush=True)
from app import main,engine,predictor,lexical,schemas,moderation_adapter,moderation_contract
modules=(main,engine,predictor,lexical,schemas,moderation_adapter,moderation_contract)
default=Path(predictor.default_model_path())
weights=[V1,default,R/'models/visobert_v2_synthetic_experiment']
paths=[Path(m.__file__) for m in modules]+[R/'app/__init__.py',SERVICE/'app/paths.py',SERVICE/'app/database.py',SERVICE/'app/review_store.py']
paths+=list((R/'tests').glob('*.py'))+list((R/'contracts').glob('*.json'))
paths+=[R/'datasets/raw/victsd/ViCTSD_test.csv',R/'datasets/raw/victsd/ViCTSD_valid.csv',R/'datasets/prepared/victsd_test.csv',R/'datasets/prepared/victsd_validation.csv']
paths+=list((R/'datasets/fixtures/genz_regression').glob('*'))
paths+=[SERVICE/'app/data/lexicon/active.json',SERVICE/'app/data/lexicon/manifest.json',SERVICE/'requirements.txt',R/'requirements-dev.txt',R/'pytest.ini']
for folder in weights:
 if folder.is_dir():paths += [p for p in folder.iterdir() if p.is_file() and p.name in ('model.safetensors','config.json','threshold_config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','sentencepiece.bpe.model')]
paths+=list(R.glob('*.sqlite3'))
paths += [p for p in (R/'services/social-api').glob('*.sqlite3')]+[p for p in (R/'services/social-api').glob('*.db')]
before=snapshot(paths);dump('protected_before.json',before)
version={n:metadata.version(n) for n in ('transformers','tokenizers','huggingface-hub','fastapi','torch','pydantic','pytest','httpx','uvicorn','safetensors','starlette')}
installed=sorted({f'{d.metadata["Name"]}=={d.version}' for d in metadata.distributions() if d.metadata.get('Name')},key=str.casefold)
(O/'installed_versions.snapshot.txt').write_text('\n'.join(installed)+'\n',encoding='utf-8')
git={}
for key,args in [('status',['git','status','--short']),('branch',['git','branch','--show-current']),('commit',['git','rev-parse','HEAD'])]:
 v=subprocess.run(args,cwd=R,capture_output=True,text=True);git[key]={'exit_code':v.returncode,'output':(v.stdout+v.stderr).strip()}
live={}
for endpoint in ('health','openapi.json'):
 try:
  with urllib.request.urlopen('http://127.0.0.1:8000/'+endpoint,timeout=3) as res:live[endpoint]={'status_code':res.status,'response':json.load(res)}
 except Exception as exc:live[endpoint]={'status':'NOT_REACHABLE','error_type':type(exc).__name__,'error':str(exc)}
config={}
for label,p in [('V1',V1),('configured_default',default),('existing_experimental_not_selected',R/'models/visobert_v2_synthetic_experiment')]:
 config[label]={'path':str(p),'weights_available':(p/'model.safetensors').is_file()}
 for name in ('config.json','threshold_config.json'):
  if (p/name).is_file():config[label][name]=json.loads((p/name).read_text(encoding='utf-8-sig'))
assert config['V1']['weights_available'] and config['V1']['threshold_config.json']['threshold']==0.41
inventory={'captured_at':now(),'client_date':'2026-11-02','python':sys.version,'executable':sys.executable,'versions':version,'git':git,
 'canonical_imports':{m.__name__:m.__file__ for m in modules},'default_checkpoint':str(default),'MODEL_PATH_override_present':bool(os.environ.get('MODEL_PATH')),
 'checkpoint_configs':config,'live_port_8000':live,'process_probe':'CIM query denied by sandbox; live localhost GET and canonical import paths recorded instead.',
 'mutation_policy':{'STORE_SUMMARIES':False,'offline':True,'training':False,'checkpoint_change':False,'test_dataset_change':False,'review_endpoints_not_called':True},
 'social_flow':'Social API worker -> authenticated POST /api/v1/moderate/comment (schema 1.0) -> advisory signals -> Social API owns visibility/audit.',
 'static_dashboard':str(SERVICE/'app/static'),'root_app_role':'compatibility import bridge'}
dump('inventory.json',inventory)
dump('openapi_snapshot.json',main.app.openapi())
dump('contract_schemas.json',{'AnalyzeRequest':schemas.AnalyzeRequest.model_json_schema(),'AnalyzeResponse':schemas.AnalyzeResponse.model_json_schema(),'ModerationRequest':moderation_contract.ModerationRequest.model_json_schema(),'ModerationResponse':moderation_contract.ModerationResponse.model_json_schema()})
dump('routes.json',{'API_routes':[{'path':path,'methods':sorted(methods)} for path,methods in main.app.openapi()['paths'].items()],'framework_and_mount_routes':[{'path':r.path,'route_class':type(r).__name__} for r in main.app.routes if hasattr(r,'path')]})
print('T020 pytest before',flush=True)
pytest_args=[sys.executable,'-X','utf8','-m','pytest','-q',str(R/'tests'),'-p','no:cacheprovider']
pre=command(pytest_args+['--basetemp',str(O/'test_tmp_before')],SERVICE,'pytest_before.txt');dump('pytest_before.json',pre)
print('PYTEST_BEFORE',pre['exit_code'],pre['summary'],flush=True)
if pre['exit_code']!=0:raise RuntimeError('Baseline tests failed; inspect evidence, do not silently fix runtime.')
from fastapi.testclient import TestClient
import torch
torch.set_num_threads(6)
inventory['torch_runtime']={'version':torch.__version__,'cuda_available':torch.cuda.is_available(),'threads':torch.get_num_threads()}
sample=json.loads((R/'examples/sample_thread.json').read_text(encoding='utf-8-sig'))
original_selector=main.default_model_path
smoke={}
# Missing-model behavior and explicitly mock-only request, in this isolated process.
main.default_model_path=lambda:str(O/'missing_checkpoint')
with TestClient(main.app) as client:
 h=client.get('/health');bad=client.post('/api/analyze',json=sample)
 assert h.status_code==200 and not h.json()['model_loaded'] and bad.status_code==503
 smoke['missing_model']={'health_status':h.status_code,'health':h.json(),'analyze_status':bad.status_code,'response':bad.json()}
 class Stub:
  name='T020 MOCK ONLY';threshold=0.41
  def predict_scores(self,texts):return [0.1]*len(texts)
 main.app.dependency_overrides[main.get_predictor]=lambda:Stub()
 result=client.post('/api/analyze',json=sample);assert result.status_code==200
 smoke['mock_only']={'status_code':result.status_code,'response':result.json(),'proves_real_inference':False}
 main.app.dependency_overrides.clear()
# CPU inference uses local checkpoints inside a fresh TestClient only; no live server is modified.
fixture_paths=sorted((R/'datasets/fixtures/genz_regression').glob('*.json'))
assert len(fixture_paths)==5
for label,folder in [('V1_immutable',V1),('V1_1_configured_default',default)]:
 print('REAL_INFERENCE_START',label,flush=True)
 main.default_model_path=lambda folder=folder:str(folder)
 os.environ['AI_SERVICE_TOKEN']=secrets.token_urlsafe(36)
 with TestClient(main.app) as client:
  h=client.get('/health');assert h.status_code==200 and h.json()['model_loaded'],h.text
  model=main.app.state.predictor;assert model.threshold==0.41
  s=client.post('/api/analyze',json=sample);assert s.status_code==200
  dump(label+'/sample_api_response.json',s.json())
  summary={'captured_at':now(),'label':label,'model_name':model.name,'threshold':model.threshold,'checkpoint_path':str(folder),'weights_sha256':sha(folder/'model.safetensors'),'health':h.json(),'fixtures':[]}
  for f in fixture_paths:
   data=json.loads(f.read_text(encoding='utf-8-sig'))
   began=time.monotonic();response=client.post('/api/analyze',json=data);assert response.status_code==200,response.text
   raw=response.json();assert len(raw['comments'])==30 and raw['model_threshold']==0.41
   dump(label+'/'+f.stem+'.response.json',raw)
   summary['fixtures'].append({'input_file':str(f.relative_to(R)),'input_sha256':sha(f),'thread_id':raw['thread_id'],'comments':len(raw['comments']),'flagged':sum(c['toxic_for_moderation'] for c in raw['comments']),'risk_level':raw['risk_level'],'suspected_repeated_harassment':raw['suspected_repeated_harassment'],'elapsed_seconds':round(time.monotonic()-began,3)})
   print('FIXTURE',label,f.stem,'HTTP',response.status_code,flush=True)
  payload=json.loads((R/'contracts/moderation_request.example.json').read_text(encoding='utf-8-sig'))
  unauthorized=client.post('/api/v1/moderate/comment',json=payload);assert unauthorized.status_code==401
  internal=client.post('/api/v1/moderate/comment',json=payload,headers={'Authorization':'Bearer '+os.environ['AI_SERVICE_TOKEN']})
  assert internal.status_code==200,internal.text
  assert internal.json()['schema_version']=='1.0'
  dump(label+'/internal_adapter_response.json',internal.json())
  summary['internal_adapter']={'unauthenticated_status':unauthorized.status_code,'authenticated_status':internal.status_code,'ephemeral_test_token_not_saved':True}
  dump(label+'/summary.json',summary);smoke[label]={'status':'REAL_INFERENCE_PASS','comments':150,'sample_http':s.status_code,'internal_http':internal.status_code,'summary_file':label+'/summary.json'}
 main.app.state.predictor=None
 gc.collect()
main.default_model_path=original_selector
assert Path(predictor.default_model_path())==default
print('T020 pytest after',flush=True)
post=command(pytest_args+['--basetemp',str(O/'test_tmp_after')],SERVICE,'pytest_after.txt');dump('pytest_after.json',post)
after=snapshot(paths);dump('protected_after.json',after)
unchanged=before==after
assert unchanged,'Protected file hash changed: inspect, do not mark complete.'
assert post['exit_code']==0,'Post baseline tests failed'
inventory['completed_at']=now();dump('inventory.json',inventory);dump('api_smoke.json',smoke)
result={'status':'PASS','task':'T020','started_at':inventory['captured_at'],'completed_at':now(),'elapsed_seconds':round(time.monotonic()-started,2),
 'pytest_before':pre,'pytest_after':post,'protected_files':len(before),'protected_hashes_unchanged':unchanged,'API_smoke':smoke,
 'current_default_unchanged':str(default),'baseline_V1_threshold':0.41,'git_available':False,'live_server_on_8000_observed':live['health']['status'] if 'status' in live['health'] else 'REACHABLE',
 'frontend_build':'NOT_RUN_no_frontend_changes','notes':['All real API inference runs used isolated in-process TestClient, no live server/default selection changed.','Fixtures are synthetic developer regression, not independent gold; no accuracy/F1 claim.','Source branch/commit unavailable because workspace is not a Git repository.','V1 and configured V1.1 baselines recorded separately; experimental V2 was only hashed, not activated or trained.']}
dump('result.json',result)
print('RESULT',json.dumps({'status':'PASS','protected_files':len(before),'protected_unchanged':unchanged,'pytest_before':pre['summary'],'pytest_after':post['summary'],'real_model_baselines':2,'synthetic_comments_per_model':150,'elapsed_seconds':result['elapsed_seconds']}),flush=True)

