"""Real wall-clock AI outage, bounded retry, offline admin and manual recovery.

Uses only temporary SQLite/accounts and an explicitly synthetic AI on recovery.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid

from run_fullstack import ROOT,SERVICE,port,ready,stop

ARTIFACTS=ROOT.parent/'ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T014_T019/outage'


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=int,default=600)
    args=parser.parse_args()
    if not 1<=args.seconds<=600:parser.error('Use 1..600 seconds')
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    env=os.environ.copy();token=secrets.token_urlsafe(32);password=secrets.token_urlsafe(24)
    env.update(PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',SOCIAL_REGISTRATION_ENABLED='true',
        SOCIAL_AUTH_RATE_LIMIT='1000',SOCIAL_CONTENT_RATE_LIMIT='1000',STORE_SUMMARIES='0',
        SHIELDVI_SYNTHETIC_AI_FIXTURE='1',AI_SERVICE_TOKEN=token,SOCIAL_AI_SERVICE_TOKEN=token,
        SOCIAL_WORKER_POLL_SECONDS='.5')
    api_port,ai_port=port(),port();base=f'http://127.0.0.1:{api_port}'
    env['SOCIAL_AI_BASE_URL']=f'http://127.0.0.1:{ai_port}'
    owned=[];logs=[];samples=[];result={'requested_outage_seconds':args.seconds,'synthetic_recovery_predictor':True,
        'real_model_inference':False,'live_db_accessed':False}
    try:
        with tempfile.TemporaryDirectory(prefix='shieldvi-T019-outage-') as temp:
            temporary=Path(temp)
            env.update(SOCIAL_DATABASE_URL='sqlite:///'+(temporary/'social.sqlite3').as_posix(),
                MODEL_PATH=str(temporary/'nonexistent-checkpoint'),REVIEW_DB_PATH=str(temporary/'ai-review.sqlite3'),
                DB_PATH=str(temporary/'ai-summary.sqlite3'))
            migration=subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=SERVICE,env=env,capture_output=True,text=True,encoding='utf-8',timeout=30)
            if migration.returncode:raise RuntimeError('Temporary schema migration failed')
            def launch(name,command,cwd,url=None):
                handle=(ARTIFACTS/f'{name}.txt').open('w',encoding='utf-8');logs.append(handle)
                proc=subprocess.Popen([sys.executable,*command],cwd=cwd,env=env,stdout=handle,stderr=subprocess.STDOUT,creationflags=flags)
                owned.append(proc)
                if url:ready(url,proc)
                return proc
            def call(method,path,data=None,bearer=None,key=False):
                headers={'Content-Type':'application/json'}
                if bearer:headers['Authorization']='Bearer '+bearer
                if key:headers['Idempotency-Key']=str(uuid.uuid4())
                request=urllib.request.Request(base+path,method=method,headers=headers,
                    data=json.dumps(data).encode() if data is not None else None)
                with urllib.request.urlopen(request,timeout=10) as response:return json.load(response)
            try:
                launch('social-api',['-m','uvicorn','shieldvi_social.main:create_app','--factory','--app-dir','src',
                    '--host','127.0.0.1','--port',str(api_port),'--no-proxy-headers'],SERVICE,base+'/health')
                for name in ('outage_author','outage_staff'):
                    call('POST','/api/v1/auth/register',{'username':name,'email':name+'@example.com','password':password})
                author=call('POST','/api/v1/auth/login',{'username':'outage_author','password':password})['access_token']
                content=call('POST','/api/v1/posts',{'body':'Temporary outage persistence fixture'},author,True)
                start=time.monotonic()
                worker=launch('worker',['-m','shieldvi_social.worker'],SERVICE)
                while True:
                    elapsed=time.monotonic()-start
                    current=call('GET',f"/api/v1/posts/{content['id']}",bearer=author)
                    assert current['visibility_status']=='PENDING_MODERATION' and current['body']=='Temporary outage persistence fixture'
                    assert worker.poll() is None
                    samples.append({'elapsed_seconds':round(elapsed,3),'visibility':current['visibility_status']})
                    (ARTIFACTS/'progress.json').write_text(json.dumps({'elapsed_seconds':round(elapsed,3),'required_seconds':args.seconds,
                        'pending_samples':len(samples),'worker_alive':True})+'\n',encoding='utf-8')
                    print(f'AI process absent: {elapsed:.1f}/{args.seconds}s; pending content retained',flush=True)
                    if elapsed>=args.seconds:break
                    deadline=min(start+args.seconds,time.monotonic()+30)
                    while time.monotonic()<deadline:time.sleep(min(1,deadline-time.monotonic()))
                result['actual_ai_absent_seconds']=time.monotonic()-start
                before=subprocess.run([sys.executable,'-m','shieldvi_social.worker','--stats'],cwd=SERVICE,env=env,
                    capture_output=True,text=True,encoding='utf-8',timeout=10)
                result['stats_before_recovery']=json.loads(before.stdout)
                launch('ai-fixture',['-m','uvicorn','ai_fixture:app','--app-dir',str(SERVICE/'tests'),
                    '--host','127.0.0.1','--port',str(ai_port),'--no-proxy-headers'],ROOT/'services/moderation-ai',env['SOCIAL_AI_BASE_URL']+'/health')
                # Provision a role only in this explicitly disposable DB, after the outage.
                from sqlalchemy import select
                from shieldvi_social.config import Settings
                from shieldvi_social.db import make_engine,session_factory
                from shieldvi_social.models import User
                engine=make_engine(Settings(database_url=env['SOCIAL_DATABASE_URL']))
                with session_factory(engine).begin() as db:
                    db.scalar(select(User).where(User.username=='outage_staff')).role='moderator'
                engine.dispose()
                staff=call('POST','/api/v1/auth/login',{'username':'outage_staff','password':password})['access_token']
                detail=call('GET',f"/api/v1/moderation/content/post/{content['id']}",bearer=staff)
                result['failed_budget_requires_manual_retry']=detail['job']['status']=='FAILED_PERMANENTLY'
                if detail['job']['status']=='FAILED_PERMANENTLY':
                    row=detail['content']
                    call('POST',f"/api/v1/moderation/jobs/{detail['job']['id']}/retry",{'expected_revision':row['content_revision'],
                        'expected_decision_version':row['decision_version'],'reason':'Synthetic AI outage recovered'},staff)
                deadline=time.monotonic()+20
                while time.monotonic()<deadline:
                    current=call('GET',f"/api/v1/posts/{content['id']}",bearer=author)
                    if current['visibility_status']=='PUBLISHED':break
                    time.sleep(.25)
                else:raise RuntimeError('Worker failed to recover after AI restart/manual retry')
                history=call('GET',f"/api/v1/moderation/content/post/{content['id']}/audit",bearer=staff)
                result.update(status='PASS',samples=samples,final_visibility=current['visibility_status'],
                    audit_events=[item['event'] for item in history['items']],worker_alive_after_recovery=worker.poll() is None,
                    no_admin_requests_during_outage=True)
                (ARTIFACTS/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
                print('PASS: AI outage retained pending content; bounded failures recovered via manual retry; no fail-open',flush=True)
            finally:
                for proc in reversed(owned):stop(proc,flags)
                for handle in logs:handle.close()
    finally:
        (ARTIFACTS/'cleanup.json').write_text(json.dumps({'owned_processes_exited':all(p.poll() is not None for p in owned),
            'temporary_db_only':True})+'\n',encoding='utf-8')


if __name__=='__main__':main()
