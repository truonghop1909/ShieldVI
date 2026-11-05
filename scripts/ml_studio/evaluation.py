"""Hashed local registry + paired synthetic holdout evaluation. Promotion is absent."""
import gc,json,os,secrets,sys,time
from collections import defaultdict
from pathlib import Path
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
from real_dataset.core import atomic_json,sha_file,now
from .datasets import DatasetStore,ROOT,digest,canonical
from .training import TrainingJobs,LOCK
sys.path.insert(0,str(ROOT/'services/moderation-ai'))
from app.model_registry import LocalModelRegistry,RegistryError

class EvaluationInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    dataset_version:str=Field(pattern=r'^[0-9a-f]{24}$')
    models:list[str]=Field(min_length=2,max_length=3)
    split:Literal['test']='test'
    processor:Literal['default-v5']='default-v5'

class EvaluationJobs:
    def __init__(self,store):self.store=store
    def catalog(self):
        pointer=self.store.root/'registry/latest.json'
        if not pointer.is_file():raise ValueError('Initialize Studio evaluation registry explicitly first')
        ref=json.loads(pointer.read_text(encoding='utf-8'));name=ref['file']
        if Path(name).name!=name:raise ValueError('Invalid registry pointer')
        path=pointer.parent/name
        if sha_file(path)!=ref['sha256']:raise ValueError('Registry hash mismatch')
        return LocalModelRegistry(path),ref['sha256']
    def initialize(self,*,allow_missing_baseline=False):
        existing=json.loads((ROOT/'configs/model_registry.repeated_recovery.local.json').read_text(encoding='utf-8'))
        models={k:existing['models'][k] for k in ('v1','v1_1','candidate_r06')}
        lock=json.loads(LOCK.read_text(encoding='utf-8'))
        for key in models:
            entry=models[key];expected=lock['models'][key]['weights_sha256']
            if entry['sha256']['model.safetensors']!=expected:raise ValueError('Baseline registry disagrees with readiness lock')
        for run in TrainingJobs(self.store).list():
            if run['status']!='COMPLETED' or not run['manifest']:continue
            path=self.store.root/'training_runs'/run['id']/'candidate';meta=run['manifest']
            models['T041_'+run['id']]={'path':str(path),'role':'experimental','threshold':.41,'approved_for_selection':False,'sha256':meta['files'],'training_run':run['id'],'dataset_sources':meta['dataset_sources']}
        manifest={'schema_version':1,'threshold':.41,'mode':'local_opt_in_only','fallback':'v1','existing_default':'v1_1','production_default_changed':False,'models':models}
        content=canonical(manifest);path=self.store.root/'registry'/('snapshot_'+digest(content)+'.json');path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():path.write_bytes(content)
        registry=LocalModelRegistry(path)
        unavailable=[]
        for key in models:
            try:registry.verify(key)
            except FileNotFoundError:
                if not allow_missing_baseline or key!='v1':raise
                # A missing optional baseline is recoverable for realtime demo,
                # but corruption in ANY remaining artifact must still fail.
                entry=models[key]
                for name,expected in entry['sha256'].items():
                    if Path(name).name!=name:raise RegistryError('Artifact name must be a basename')
                    artifact=Path(entry['path'])/name
                    if artifact.exists() and sha_file(artifact)!=expected:raise RegistryError('Checkpoint integrity mismatch')
                unavailable.append(key)
        atomic_json(path.parent/'latest.json',{'file':path.name,'sha256':sha_file(path)})
        with self.store.connect() as db:db.execute('CREATE TABLE IF NOT EXISTS evaluation_runs(id TEXT PRIMARY KEY,status TEXT NOT NULL,config_json TEXT NOT NULL,registry_sha TEXT NOT NULL,owner_id TEXT NOT NULL,created_at TEXT NOT NULL,heartbeat REAL,error_code TEXT)')
        return {'models':list(models),'registry_sha256':sha_file(path),'default_unchanged':True,
            'evaluation_enabled':not unavailable,'unavailable_models':unavailable}
    def list_models(self):
        registry,sha=self.catalog()
        unavailable=[key for key,entry in registry.models.items() if any(not (Path(entry['path'])/name).is_file() for name in entry['sha256'])]
        blocked=registry.fallback in unavailable
        return {'registry_sha256':sha,'default':'v1_1','activation_enabled':False,'formal_gate':'BLOCKED_T028_NO_HUMAN_GOLD',
            'evaluation_enabled':not blocked,'evaluation_blocker':'ORIGINAL_V1_UNAVAILABLE' if blocked else None,
            'models':[{'id':k,'role':v['role'],'available':k not in unavailable,'state':'UNAVAILABLE' if k in unavailable else 'CANDIDATE' if v['role']=='experimental' else 'APPROVED_EXISTING' if k in ('v1','v1_1') else 'RESEARCH',
            'weights_sha256':v['sha256']['model.safetensors'],'threshold':v['threshold'],'training_run':v.get('training_run'),'dataset_sources':v.get('dataset_sources'),'promotable':False} for k,v in registry.models.items()]}
    def preflight(self,value):
        value=EvaluationInput.model_validate(value);registry,sha=self.catalog()
        if len(set(value.models))!=len(value.models) or any(k not in registry.models for k in value.models):raise ValueError('Choose distinct registered models')
        try:registry.verify(registry.fallback)
        except (OSError,ValueError) as exc:raise ValueError('Original V1 unavailable or invalid; evaluation and rollback remain blocked. Restore the original artifacts, not a substitute model.') from exc
        for key in value.models:registry.verify(key)
        record=self.store.get(value.dataset_version)
        if record['status']!='ACCEPTED' or record['manifest']['data_origin']!='synthetic' or not record['manifest']['split_locked']:raise ValueError('Only locked accepted synthetic development holdouts are eligible here')
        rows=[r for r in self.store.rows(value.dataset_version) if r['split']=='test']
        if not rows or len(rows)>200:raise ValueError('Expected 1–200 locked test-partition comments')
        if any(r['label'] is None for r in rows):raise ValueError('Holdout reference labels missing')
        return value,sha
    def create(self,value,owner):
        value,sha=self.preflight(value);identity=secrets.token_hex(12);path=self.store.root/'evaluations'/identity;path.mkdir(parents=True)
        atomic_json(path/'config.json',value.model_dump())
        with self.store.connect() as db:db.execute('INSERT INTO evaluation_runs VALUES(?,?,?,?,?,?,?,?)',(identity,'QUEUED',json.dumps(value.model_dump()),sha,owner,now(),time.time(),None));self.store.audit(db,owner,'SYNTHETIC_EVALUATION_QUEUED',identity,{'registry_sha256':sha})
        return self.get(identity)
    def get(self,identity):
        if len(identity)!=24 or any(c not in '0123456789abcdef' for c in identity):raise KeyError('Unknown evaluation')
        with self.store.connect() as db:row=db.execute('SELECT * FROM evaluation_runs WHERE id=?',(identity,)).fetchone()
        if not row:raise KeyError('Unknown evaluation')
        value=dict(row);value['config']=json.loads(value.pop('config_json'));path=self.store.root/'evaluations'/identity/'report.json';value['report']=json.loads(path.read_text(encoding='utf-8')) if path.exists() else None;return value
    def list(self):
        with self.store.connect() as db:rows=db.execute('SELECT id FROM evaluation_runs ORDER BY created_at DESC LIMIT 100').fetchall()
        return [self.get(r['id']) for r in rows]
    def run_once(self):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE');db.execute("UPDATE evaluation_runs SET status='FAILED',error_code='INTERRUPTED' WHERE status='RUNNING' AND heartbeat<?",(time.time()-900,))
            if db.execute("SELECT 1 FROM evaluation_runs WHERE status='RUNNING'").fetchone():return False
            row=db.execute("SELECT id FROM evaluation_runs WHERE status='QUEUED' ORDER BY created_at LIMIT 1").fetchone()
            if not row:return False
            identity=row['id'];db.execute("UPDATE evaluation_runs SET status='RUNNING',heartbeat=? WHERE id=?",(time.time(),identity))
        try:
            report=self.evaluate(self.get(identity));atomic_json(self.store.root/'evaluations'/identity/'report.json',report);status='COMPLETED';error=None
        except Exception as exc:status='FAILED';error=type(exc).__name__
        with self.store.connect() as db:db.execute('UPDATE evaluation_runs SET status=?,error_code=? WHERE id=?',(status,error,identity));self.store.audit(db,'local-evaluation-worker','EVALUATION_'+status,identity,{'error_type':error})
        return True
    def evaluate(self,run):
        value,sha=self.preflight(run['config'])
        if sha!=run['registry_sha']:raise ValueError('Registry changed after evaluation was queued')
        registry,_=self.catalog();rows=[r for r in self.store.rows(value.dataset_version) if r['split']=='test'];groups=defaultdict(list)
        for row in rows:groups[row['thread_id']].append(row)
        import torch
        torch.set_num_threads(2)
        from app.live_analysis import IncrementalAnalyzer
        from app.moderation_contract import ModerationRequest
        from evaluate_synthetic_signals import classification
        output={};all_errors=[];scores={}
        for model_id in value.models:
            started=time.perf_counter();predictor,loaded=registry.load(model_id,shadow=True)
            if loaded['selected']!=model_id:raise ValueError('Requested evaluation model failed to load; fallback cannot impersonate it')
            analyzer=IncrementalAnalyzer(predictor);raw=[];final=[];predictions=[];target_total=target_correct=0;emitted=0;reference_pairs=defaultdict(set);events=set();evidence_total=evidence_correct=0;raw_scores=[]
            for tid,thread in groups.items():
                idmap={r['comment_id']:'C_'+digest((tid+':'+r['comment_id']).encode())[:20] for r in thread};truth={idmap[r['comment_id']]:r for r in thread};prior=[]
                for row in thread:
                    previous=prior[-50:];visible={r['comment_id'] for r in previous}
                    comments=[{k:r[k] for k in ('comment_id','user_id','text','timestamp','parent_id')} for r in previous]
                    for item in comments:
                        if item['parent_id'] not in visible:item['parent_id']=None
                    parent=idmap.get(row['parent_id']);current_id=idmap[row['comment_id']]
                    request=ModerationRequest(schema_version='1.0',request_id='E_'+secrets.token_hex(12),content_id=current_id,content_revision=1,user_id=row['user_id'],text=row['text'],timestamp=row['timestamp'],parent_id=parent if parent in visible else None,context={'post_id':'T_'+digest(tid.encode())[:20],'complete':len(prior)<=50,'recent_comments':comments})
                    response=analyzer.analyze(request);advice=response.conversation_signals.current;raw.append((row['label'],response.ai_label));final.append((row['label'],advice.assessment_label));raw_scores.append(response.toxicity_score)
                    predicted=advice.directed_at_user_id;emitted+=int(predicted is not None)
                    if row['target_user_id'] is not None:target_total+=1;target_correct+=int(predicted==row['target_user_id']);reference_pairs[(tid,row['user_id'],row['target_user_id'])].add(row['timestamp'])
                    for e in response.evidence:
                        event=e.model_dump() if hasattr(e,'model_dump') else e;events.add((tid,event['actor_user_id'],event['target_user_id']))
                        for cid in event['evidence_comment_ids']:
                            expected=truth.get(cid)
                            if expected and expected['target_user_id'] is not None:evidence_total+=1;evidence_correct+=int(expected['label']=='TOXIC' and expected['user_id']==event['actor_user_id'] and expected['target_user_id']==event['target_user_id'])
                    predictions.append({'thread_id':tid,'comment_id':row['comment_id'],'reference':row['label'],'raw_score':response.toxicity_score,'raw_label':response.ai_label,'final_label':advice.assessment_label,'reply_recipient':advice.reply_to_user_id,'directed_target':predicted,'attack_instance':advice.attack_instance_candidate,'context':advice.model_dump(),'lexical':response.model_dump(mode='json')['lexical_signals'],'policy':{'risk':advice.policy_risk,'executed':False}})
                    if row['label']!='UNCERTAIN' and advice.assessment_label!=row['label']:all_errors.append({'model':model_id,'thread_id':tid,'comment_id':row['comment_id'],'reference':row['label'],'prediction':advice.assessment_label,'text':row['text']})
                    prior.append({'comment_id':current_id,'user_id':row['user_id'],'text':row['text'],'timestamp':row['timestamp'],'parent_id':parent})
            expected={p for p,t in reference_pairs.items() if len(t)>=2};matched=len(events&expected)
            output[model_id]={'raw':classification(raw),'final':classification(final),'uncertain_excluded':sum(r['label']=='UNCERTAIN' for r in rows),'weights_sha256':registry.models[model_id]['sha256']['model.safetensors'],
                'target':{'reference_targets':target_total,'correct':target_correct,'emitted':emitted,'recall':target_correct/target_total if target_total else None,'note':'Target labels are absent when denominator0; no inferred human/reference target labels'},
                'repeated':{'reference_events':len(expected),'emitted':len(events),'precision':matched/len(events) if events and reference_pairs else None,'recall':matched/len(expected) if expected else None},
                'evidence':{'scored':evidence_total,'correct':evidence_correct,'correctness':evidence_correct/evidence_total if evidence_total else None},'predictions':predictions,'elapsed_ms':(time.perf_counter()-started)*1000}
            scores[model_id]=raw_scores;del analyzer,predictor;gc.collect()
        # Existing verified loader exercises actual local fallback; never changes a service selector.
        from app.predictor import ViSoBERTPredictor
        candidate=next(k for k in reversed(value.models) if k!='v1');candidate_path=registry.models[candidate]['path']
        def injected_loader(path):
            if path==candidate_path:raise RuntimeError('Deliberate local shadow loader failure')
            return ViSoBERTPredictor(path)
        rollback,trace=registry.load(candidate,shadow=True,loader=injected_loader);probes=rollback.predict_scores([r['text'] for r in rows[:2]]);del rollback;gc.collect()
        report={'schema_version':'studio-evaluation-1.0','scope':'synthetic_development_not_independent_real','human_gold':False,'dataset_version':value.dataset_version,'dataset_sha256':self.store.get(value.dataset_version)['manifest']['normalized_sha256'],'split':'locked_test','comments':len(rows),'registry_sha256':sha,'models':output,'errors':all_errors,
            'shadow':{'mode':'paired_offline_actual_neural_inference_same_inputs','scores':scores,'production_changed':False},'rollback':{**trace,'probe_count':len(probes),'actual_neural_inference':True},'promotion':'BLOCKED_NO_INDEPENDENT_HUMAN_GOLD','threshold':.41,'default_unchanged':True}
        atomic_json(self.store.root/'evaluations'/run['id']/'development_exclusion.json',{'dataset_version':value.dataset_version,'source_sha256':report['dataset_sha256'],'role':'exposed_synthetic_development_not_independent','human_gold':False})
        return report

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--initialize-only',action='store_true');parser.add_argument('--once',action='store_true');args=parser.parse_args()
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='-1',TOKENIZERS_PARALLELISM='false');jobs=EvaluationJobs(DatasetStore(args.root))
    if args.initialize_only:print(json.dumps(jobs.initialize()));raise SystemExit(0)
    while True:
        jobs.run_once()
        if args.once:break
        time.sleep(.5)
