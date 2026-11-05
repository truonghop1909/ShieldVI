"""Durable local CPU job controller. No torch import in the HTTP process."""
import json,os,secrets,shutil,subprocess,sys,time
from pathlib import Path
from typing import Literal
from uuid import UUID
from pydantic import BaseModel,ConfigDict,Field
from real_dataset.core import atomic_json,sha_file,now
from .datasets import DatasetStore,ROOT,canonical,digest
LOCK=ROOT/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json'

class TrainingInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    dataset_versions:list[str]=Field(min_length=1,max_length=4)
    mode:Literal['synthetic-only']='synthetic-only'
    base_model:Literal['V1']='V1'
    strategy:Literal['head-only-cpu']='head-only-cpu'
    epochs:int=Field(default=1,ge=1,le=3)
    learning_rate:float=Field(default=.00003,ge=.000001,le=.001,allow_inf_nan=False)
    batch_size:int=Field(default=8,ge=4,le=32)
    max_length:int=Field(default=64,ge=32,le=128)
    cpu_threads:int=Field(default=2,ge=1,le=4)
    max_seconds:int=Field(default=180,ge=60,le=900)
    seed:int=Field(default=20261104,ge=0,le=2147483647)
    balanced_class_weights:bool=False
    early_stopping_patience:int=Field(default=2,ge=1,le=3)

def base_checkpoint():
    record=json.loads(LOCK.read_text(encoding='utf-8'))['models']['v1'];path=Path(record['path'])
    if sha_file(path/'model.safetensors')!=record['weights_sha256']:raise ValueError('Protected V1 checkpoint hash mismatch')
    config=path/'threshold_config.json'
    if config.exists() and json.loads(config.read_text(encoding='utf-8'))['threshold']!=.41:raise ValueError('V1 threshold mismatch')
    for name in ('config.json','tokenizer_config.json'):
        if not (path/name).is_file():raise ValueError('V1 tokenizer/model metadata incomplete')
    return path,record

class TrainingJobs:
    def __init__(self,store):self.store=store
    def preflight(self,value):
        value=TrainingInput.model_validate(value)
        if len(set(value.dataset_versions))!=len(value.dataset_versions):raise ValueError('Duplicate dataset versions')
        rows=[];sources={};seen=set();threads=set()
        for identity in value.dataset_versions:
            record=self.store.get(identity)
            if record['status']!='ACCEPTED' or not record['report']['training_eligible'] or record['manifest']['data_origin']!='synthetic':raise ValueError('Dataset must be accepted binary synthetic with no unresolved warnings/rights/PII/leakage issues')
            for row in self.store.rows(identity):
                key=digest(row['text'].strip().casefold().encode())
                if key in seen:raise ValueError('Cross-dataset exact text overlap')
                seen.add(key);rows.append(row)
            source=self.store.root/'versions'/identity/'comments.jsonl';sources[identity]={'path':str(source),'sha256':sha_file(source)}
        for split in ('train','validation'):
            labels={r['label'] for r in rows if r['split']==split}
            if labels!={'CLEAN','TOXIC'}:raise ValueError(f'{split} must contain both binary classes in locked thread splits')
        base,record=base_checkpoint();required=2*(base/'model.safetensors').stat().st_size+134217728
        if shutil.disk_usage(self.store.root).free<required:raise ValueError('Insufficient free disk for an isolated candidate')
        return {'passed':True,'scope':'synthetic_development_smoke_not_real_acceptance','training_authorization':'current_user_T041_bounded_CPU_head_only_not_r07',
                'base_path':str(base),'base_sha256':record['weights_sha256'],'threshold':.41,'sources':sources,'exclusions_sha256':self.store.marker['exclusions_sha256'],
                'counts':{k:sum(r['split']==k for r in rows) for k in ('train','validation','test')},'estimated_min_disk_bytes':required,'estimated_ram_bytes':3*(base/'model.safetensors').stat().st_size,'gpu':False,'external_cost':0}
    def create(self,value,owner,key):
        value=TrainingInput.model_validate(value);key=str(UUID(str(key)));config=value.model_dump()
        with self.store.connect() as db:old=db.execute('SELECT * FROM training_runs WHERE owner_id=? AND idempotency_key=?',(owner,key)).fetchone()
        if old:
            if json.loads(old['config_json'])!=config:raise ValueError('Idempotency key reused with different configuration')
            return self.get(old['id'])
        preflight=self.preflight(value);identity=secrets.token_hex(12);stamp=now()
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE');old=db.execute('SELECT * FROM training_runs WHERE owner_id=? AND idempotency_key=?',(owner,key)).fetchone()
            if old:
                if json.loads(old['config_json'])!=config:raise ValueError('Idempotency key conflict')
                return self.get(old['id'])
            path=self.store.root/'training_runs'/identity;path.mkdir(parents=True,exist_ok=False)
            atomic_json(path/'config.json',config);atomic_json(path/'preflight.json',preflight)
            db.execute('INSERT INTO training_runs VALUES(?,?,?,?,?,?,?,?,?,?)',(identity,owner,key,json.dumps(config),json.dumps(preflight),'QUEUED',stamp,stamp,None,None));self.store.audit(db,owner,'TRAINING_QUEUED',identity,{'config_sha256':digest(canonical(config))})
        return self.get(identity)
    def get(self,identity):
        if len(identity)!=24 or any(c not in '0123456789abcdef' for c in identity):raise KeyError('Unknown training run')
        with self.store.connect() as db:row=db.execute('SELECT * FROM training_runs WHERE id=?',(identity,)).fetchone()
        if not row:raise KeyError('Unknown training run')
        value=dict(row);value.pop('idempotency_key');value['config']=json.loads(value.pop('config_json'));value['preflight']=json.loads(value.pop('preflight_json'))
        report=self.store.root/'training_runs'/identity/'candidate/training_report.json'
        value['metrics']=json.loads(report.read_text(encoding='utf-8')) if report.exists() else None
        manifest=self.store.root/'training_runs'/identity/'run_manifest.json';value['manifest']=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else None
        return value
    def list(self):
        with self.store.connect() as db:rows=db.execute('SELECT id FROM training_runs ORDER BY created_at DESC LIMIT 100').fetchall()
        return [self.get(row['id']) for row in rows]
    def cancel(self,identity,actor):
        self.get(identity)
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE');row=db.execute('SELECT status FROM training_runs WHERE id=?',(identity,)).fetchone()
            if row['status'] in ('QUEUED','RUNNING'):db.execute('UPDATE training_runs SET status=?,updated_at=? WHERE id=?',('CANCELLED' if row['status']=='QUEUED' else 'CANCELLING',now(),identity));self.store.audit(db,actor,'TRAINING_CANCEL_REQUESTED',identity,{})
        return self.get(identity)
    def run_once(self):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            # A crashed worker may leave its CPU child alive until its own deadline.
            # Wait longer than the maximum budget before marking interrupted; never retry it silently.
            db.execute("UPDATE training_runs SET status='FAILED',error_code='WORKER_INTERRUPTED',updated_at=? WHERE status IN ('RUNNING','CANCELLING') AND heartbeat<?",(now(),time.time()-1020))
            if db.execute("SELECT 1 FROM training_runs WHERE status IN ('RUNNING','CANCELLING')").fetchone():return False
            row=db.execute("SELECT id FROM training_runs WHERE status='QUEUED' ORDER BY created_at LIMIT 1").fetchone()
            if not row:return False
            identity=row['id'];db.execute("UPDATE training_runs SET status='RUNNING',heartbeat=?,updated_at=? WHERE id=?",(time.time(),now(),identity))
        value=self.get(identity);path=self.store.root/'training_runs'/identity;env=os.environ.copy()
        env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='-1',TOKENIZERS_PARALLELISM='false',OMP_NUM_THREADS=str(value['config']['cpu_threads']),MKL_NUM_THREADS=str(value['config']['cpu_threads']),PYTHONIOENCODING='utf-8')
        process=None;code=None;status='FAILED';started=time.monotonic()
        try:
            with (path/'worker.log').open('w',encoding='utf-8') as log:
                process=subprocess.Popen([sys.executable,'-m','ml_studio.train_child','--root',str(self.store.root),'--run-id',identity],env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,creationflags=(subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS) if os.name=='nt' else 0)
                while process.poll() is None:
                    current=self.get(identity)['status']
                    if current=='CANCELLING':status='CANCELLED';code='CANCELLED_BY_OPERATOR';break
                    if time.monotonic()-started>value['config']['max_seconds']:code='CPU_RUNTIME_LIMIT';break
                    with self.store.connect() as db:db.execute('UPDATE training_runs SET heartbeat=? WHERE id=?',(time.time(),identity))
                    time.sleep(.25)
                if process.poll() is None:process.terminate();process.wait(timeout=10)
                if code is None:
                    result=self.get(identity);manifest=result['manifest'];report=result['metrics']
                    if process.returncode==0 and manifest and report and report['training_performed'] and report['encoder_unchanged'] and report['reload_probe_max_error']<=1e-5 and sha_file(path/'candidate/model.safetensors')==manifest['candidate_sha256']:status='COMPLETED'
                    else:code='CHILD_FAILED_OR_UNVERIFIED_ARTIFACTS'
        except BaseException:
            code='WORKER_ERROR'
            if process and process.poll() is None:process.kill();process.wait(timeout=10)
        finally:
            with self.store.connect() as db:
                current=db.execute('SELECT status FROM training_runs WHERE id=?',(identity,)).fetchone()['status']
                if current=='CANCELLING':status='CANCELLED'
                db.execute('UPDATE training_runs SET status=?,error_code=?,updated_at=?,heartbeat=? WHERE id=?',(status,code,now(),time.time(),identity));self.store.audit(db,'local-cpu-worker','TRAINING_'+status,identity,{'error_code':code})
        return True

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--once',action='store_true');args=parser.parse_args();jobs=TrainingJobs(DatasetStore(args.root))
    while True:
        jobs.run_once()
        if args.once:break
        time.sleep(.5)
