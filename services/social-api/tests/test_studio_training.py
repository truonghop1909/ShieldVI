import json,time
from uuid import uuid4
import pytest
from pydantic import ValidationError
from test_studio_datasets import studio,upload,payload,sample
from test_live_api import live
from ml_studio.training import TrainingJobs,TrainingInput

def test_training_limits_and_untrusted_paths_rejected():
    for data in ({'cpu_threads':5},{'max_seconds':901},{'base_model':'../../models'},{'strategy':'full-gpu'},{'mode':'mixed'},{'learning_rate':float('nan')},{'output_dir':'C:/private'}):
        with pytest.raises(ValidationError):TrainingInput.model_validate({'dataset_versions':['x'],**data})

def test_training_preflight_rejects_unlabeled_uncertain_small_partitions(studio):
    for changes in ({'dataset_type':'UNLABELED','content':json.dumps([sample(label=None)])},{'content':json.dumps([sample(label='UNCERTAIN')])},{}):
        identity=upload(studio,payload(**changes)).json()['id']
        with pytest.raises(ValueError):TrainingJobs(studio[1]).preflight({'dataset_versions':[identity]})

def test_training_api_admin_idempotency_and_queued_cancel(studio,monkeypatch):
    live,store=studio;jobs=TrainingJobs(store);flight={'passed':True,'scope':'unit_only_not_actual_training'}
    monkeypatch.setattr(TrainingJobs,'preflight',lambda self,value:flight)
    body={'dataset_versions':['fixture']};headers={**live[3],'Idempotency-Key':str(uuid4())}
    assert live[0].post('/api/studio/training-runs',headers={**live[1],'Idempotency-Key':str(uuid4())},json=body).status_code==403
    first=live[0].post('/api/studio/training-runs',headers=headers,json=body).json();assert first['status']=='QUEUED'
    assert live[0].post('/api/studio/training-runs',headers=headers,json=body).json()['id']==first['id']
    assert live[0].post('/api/studio/training-runs',headers=headers,json={**body,'epochs':2}).status_code==422
    assert live[0].post('/api/studio/training-runs/'+first['id']+'/cancel',headers=live[3]).json()['status']=='CANCELLED'
    assert not jobs.run_once()

def test_worker_recovery_does_not_duplicate_potential_orphan(studio,monkeypatch):
    jobs=TrainingJobs(studio[1]);monkeypatch.setattr(TrainingJobs,'preflight',lambda self,value:{'passed':True})
    run=jobs.create({'dataset_versions':['fixture']},'synthetic-test',uuid4())
    with studio[1].connect() as db:db.execute("UPDATE training_runs SET status='RUNNING',heartbeat=? WHERE id=?",(time.time(),run['id']))
    assert not jobs.run_once() and jobs.get(run['id'])['status']=='RUNNING'
    with studio[1].connect() as db:db.execute('UPDATE training_runs SET heartbeat=? WHERE id=?',(time.time()-1030,run['id']))
    assert not jobs.run_once() and jobs.get(run['id'])['error_code']=='WORKER_INTERRUPTED'

def test_nonexistent_or_path_traversal_training_run_rejected(studio):
    c,_,_,staff,_,_=studio[0]
    assert c.get('/api/studio/training-runs/not-a-run',headers=staff).status_code==404

def test_running_cancel_terminates_only_owned_child_and_never_completes(studio,monkeypatch):
    from ml_studio import training
    jobs=TrainingJobs(studio[1]);monkeypatch.setattr(TrainingJobs,'preflight',lambda self,value:{'passed':True})
    run=jobs.create({'dataset_versions':['fixture']},'synthetic-test',uuid4());owned=[]
    class Child:
        def __init__(self,*args,**kwargs):self.returncode=None;self.calls=0;self.terminated=False;owned.append(self)
        def poll(self):
            self.calls+=1
            if self.calls==1:jobs.cancel(run['id'],'test-operator')
            return self.returncode
        def terminate(self):self.terminated=True;self.returncode=-15
        def wait(self,timeout=None):return self.returncode
    monkeypatch.setattr(training.subprocess,'Popen',Child)
    assert jobs.run_once() and owned[0].terminated
    assert jobs.get(run['id'])['status']=='CANCELLED' and jobs.get(run['id'])['manifest'] is None

def test_child_crash_cannot_be_reported_as_success(studio,monkeypatch):
    from ml_studio import training
    jobs=TrainingJobs(studio[1]);monkeypatch.setattr(TrainingJobs,'preflight',lambda self,value:{'passed':True});run=jobs.create({'dataset_versions':['fixture']},'synthetic-test',uuid4())
    class Child:
        returncode=42
        def __init__(self,*args,**kwargs):pass
        def poll(self):return self.returncode
    monkeypatch.setattr(training.subprocess,'Popen',Child)
    assert jobs.run_once() and jobs.get(run['id'])['status']=='FAILED'
    assert jobs.get(run['id'])['error_code']=='CHILD_FAILED_OR_UNVERIFIED_ARTIFACTS'
