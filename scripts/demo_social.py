"""Real CPU AI + worker + two UIs, with disposable accounts/DB and ai-off/on.
Run with the Social API venv. No downloads, training or live DB migration.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid

ROOT=Path(__file__).resolve().parents[1]
SERVICE=ROOT/'services/social-api'
AI=ROOT/'services/moderation-ai'
CONTROL_COMMANDS=('ai-off','ai-on','status','quit')


def assert_repeated_evidence(ai):
    assert ai.get('suspected_repeated_harassment') is True, (
        'D FAIL: Repeated harassment not detected'
    )
    evidence = ai.get('evidence') or []
    repeated_evidence = [
        e for e in evidence
        if e.get('n_distinct_timestamps', 0) >= 2
    ]
    assert repeated_evidence, 'D FAIL: No repeated harassment evidence'
    assert any(
        len(set(e.get('evidence_comment_ids') or [])) >= 2
        for e in repeated_evidence
    ), 'D FAIL: Missing or insufficient evidence_comment_ids'


def send_control(path,command):
    path=Path(path).absolute()
    resolved=path.resolve()
    if (path.is_symlink() or resolved.name!='demo-control.jsonl' or
        not resolved.parent.name.startswith('shieldvi-live-demo-') or
        Path(tempfile.gettempdir()).resolve() not in resolved.parents or not resolved.is_file()):
        raise ValueError('Use the control file printed by the active --no-console demo')
    if command not in CONTROL_COMMANDS:raise ValueError('Unsupported demo command')
    with resolved.open('a',encoding='utf-8') as handle:
        handle.write(json.dumps({'command':command})+'\n')


def read_external_commands(path):
    offset=0
    while True:
        with path.open(encoding='utf-8') as handle:
            handle.seek(offset);line=handle.readline()
            complete=line.endswith('\n')
            if complete:offset=handle.tell()
        if not complete:
            time.sleep(.2);continue
        try:command=json.loads(line).get('command')
        except (ValueError,AttributeError):command=None
        if command in CONTROL_COMMANDS:yield command


def ports():
    sockets=[]
    try:
        for _ in range(4):
            sock=socket.socket();sock.bind(('127.0.0.1',0));sockets.append(sock)
        return [sock.getsockname()[1] for sock in sockets]
    finally:
        for sock in sockets:sock.close()


class Demo:
    def __init__(self,folder):
        self.folder=Path(folder).resolve();self.flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        self.owned=[];self.logs=[];self.ai=None
        self.api_port,self.ai_port,self.social_port,self.admin_port=ports()
        self.api=f'http://127.0.0.1:{self.api_port}'
        self.ai_url=f'http://127.0.0.1:{self.ai_port}'
        self.social=f'http://127.0.0.1:{self.social_port}';self.admin=f'http://127.0.0.1:{self.admin_port}'
        self.node=shutil.which('node');self.ai_python=ROOT/('.venv/Scripts/python.exe' if os.name=='nt' else '.venv/bin/python')
        if not self.node or not self.ai_python.is_file():raise RuntimeError('Node or existing AI venv missing')
        checkpoint=ROOT/'models/visobert_head_refined'
        cfg=json.loads((checkpoint/'threshold_config.json').read_text(encoding='utf-8'))
        if cfg.get('approval_status')!='approved' or cfg.get('threshold')!=.41 or not (checkpoint/'model.safetensors').is_file():
            raise RuntimeError('Need the existing approved local checkpoint at 0.41')
        self.password=secrets.token_urlsafe(18);key=secrets.token_urlsafe(32);self.env=os.environ.copy()
        for name in ('MODEL_PATH','PYTHONPATH','SHIELDVI_FULLSTACK_E2E','SHIELDVI_SYNTHETIC_AI_FIXTURE'):self.env.pop(name,None)
        self.env.update(PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
            HF_HUB_DISABLE_TELEMETRY='1',CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',STORE_SUMMARIES='0',
            SOCIAL_DATABASE_URL='sqlite:///'+(self.folder/'social-demo.sqlite3').as_posix(),
            DB_PATH=str(self.folder/'ai-summary.sqlite3'),REVIEW_DB_PATH=str(self.folder/'ai-review.sqlite3'),
            SOCIAL_REGISTRATION_ENABLED='false',VITE_REGISTRATION_ENABLED='false',SOCIAL_CORS_ORIGINS='[]',
            VITE_SOCIAL_API_BASE='',SOCIAL_API_PROXY_TARGET=self.api,SOCIAL_AI_BASE_URL=self.ai_url,
            AI_SERVICE_TOKEN=key,SOCIAL_AI_SERVICE_TOKEN=key,SOCIAL_AUTH_RATE_LIMIT='1000',SOCIAL_CONTENT_RATE_LIMIT='1000',
            AI_SERVICE_RATE_LIMIT='1000',SOCIAL_WORKER_POLL_SECONDS='.5',SOCIAL_WORKER_MAX_ATTEMPTS='3',
            SOCIAL_AI_CONNECT_TIMEOUT='3',SOCIAL_AI_READ_TIMEOUT='60',SOCIAL_WORKER_LEASE_SECONDS='180')

    def command(self,args):
        result=subprocess.run([sys.executable,*args],cwd=SERVICE,env=self.env,capture_output=True,text=True,encoding='utf-8',timeout=30,creationflags=self.flags)
        if result.returncode:raise RuntimeError('Demo migration/worker command failed')
        return result.stdout

    def launch(self,name,args,cwd,url=None,model=False):
        handle=(self.folder/f'{name}-{len(self.owned)}.log').open('w',encoding='utf-8');self.logs.append(handle)
        # Vite binds readline shortcuts to an inherited TTY. Only this parent
        # controller may read the user's keyboard; all child servers are headless.
        proc=subprocess.Popen(args,cwd=cwd,env=self.env,stdin=subprocess.DEVNULL,
            stdout=handle,stderr=subprocess.STDOUT,creationflags=self.flags);self.owned.append(proc)
        if url:
            deadline=time.monotonic()+120
            while time.monotonic()<deadline:
                if proc.poll() is not None:raise RuntimeError(f'{name} exited during startup')
                try:
                    with urllib.request.urlopen(url,timeout=2) as response:
                        if response.status==200:
                            if model and not json.load(response).get('model_loaded'):raise RuntimeError('Real model unavailable')
                            return proc
                except OSError:time.sleep(.25)
            raise RuntimeError(f'{name} startup timed out')
        return proc

    def stop(self,proc):
        if proc is None:return
        if proc.poll() is None:
            if os.name=='nt':subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,creationflags=self.flags)
            else:proc.terminate()
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)

    def ai_off(self):self.stop(self.ai);self.ai=None

    def ai_on(self):
        if self.ai and self.ai.poll() is None:return
        self.ai=self.launch('ai',[str(self.ai_python),'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(self.ai_port),
            '--no-proxy-headers'],AI,self.ai_url+'/health',True)

    def start(self):
        self.command(['-m','alembic','upgrade','head'])
        from shieldvi_social.config import Settings
        from shieldvi_social.db import make_engine,session_factory
        from shieldvi_social.models import User
        from shieldvi_social.security import PASSWORD_HASHER
        engine=make_engine(Settings(database_url=self.env['SOCIAL_DATABASE_URL']))
        try:
            if Path(engine.url.database).resolve().parent!=self.folder:raise RuntimeError('Unsafe demo DB path')
            with session_factory(engine).begin() as db:
                for name,role in (('demo_alice','user'),('demo_bob','user'),('demo_admin','admin')):
                    db.add(User(username=name,email=name+'@example.com',role=role,password_hash=PASSWORD_HASHER.hash(self.password)))
        finally:engine.dispose()
        self.launch('social-api',[sys.executable,'-m','uvicorn','shieldvi_social.main:create_app','--factory','--app-dir','src',
            '--host','127.0.0.1','--port',str(self.api_port),'--no-proxy-headers'],SERVICE,self.api+'/health')
        self.ai_on()
        for name,port,url in (('social-web',self.social_port,self.social),('moderation-web',self.admin_port,self.admin)):
            web=ROOT/'apps'/name
            self.launch(name,[self.node,str(web/'node_modules/vite/bin/vite.js'),'--port',str(port),'--strictPort','--configLoader','runner'],web,url)
        self.worker=self.launch('worker',[sys.executable,'-m','shieldvi_social.worker'],SERVICE)

    def close(self):
        for proc in reversed(self.owned):self.stop(proc)
        for log in self.logs:log.close()

    def stats(self):return json.loads(self.command(['-m','shieldvi_social.worker','--stats']))

    def call(self,path,body=None,token=None,create=False):
        headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        if create:headers['Idempotency-Key']=str(uuid.uuid4())
        request=urllib.request.Request(self.api+'/api/v1'+path,headers=headers,method='POST' if body is not None else 'GET',
            data=json.dumps(body).encode() if body is not None else None)
        with urllib.request.urlopen(request,timeout=15) as response:return json.load(response)

    def wait(self,kind,row,token):
        deadline=time.monotonic()+100
        while time.monotonic()<deadline:
            row=self.call(f'/{kind}s/{row["id"]}',token=token)
            if row['visibility_status']!='PENDING_MODERATION':return row
            if self.worker.poll() is not None:raise RuntimeError('Worker stopped')
            time.sleep(.5)
        raise RuntimeError('Still pending; inspect AI errors/retry budget')

    def smoke(self):
        alice,bob,admin=(self.call('/auth/login',{'username':name,'password':self.password})['access_token']
            for name in ('demo_alice','demo_bob','demo_admin'))
        versions=lambda row:{'expected_revision':row['content_revision'],'expected_decision_version':row['decision_version']}
        def create(text,post_id=None,parent=None,token=alice):
            kind='comment' if post_id else 'post';path=f'/posts/{post_id}/comments' if post_id else '/posts'
            row=self.call(path,{'body':text,**({'parent_id':parent} if post_id else {})},token,True)
            assert row['visibility_status']=='PENDING_MODERATION'
            return self.wait(kind,row,token)
        post=create('Xin chào, cảm ơn bạn.');clean=create('Xin chào, cảm ơn bạn.',post['id'])
        assert post['visibility_status']==clean['visibility_status']=='PUBLISHED'
        print('A PASS: benign post/comment published by real AI',flush=True)
        toxic=create('Mày đúng là đồ ngu.',post['id'])
        detail=self.call(f'/moderation/content/comment/{toxic["id"]}',token=admin)
        assert detail['ai']['ai_label']=='TOXIC' and toxic['risk_tier']=='REVIEW' and toxic['visibility_status']=='PUBLISHED_FLAGGED'
        print('B PASS: AI label, policy risk and visibility are separate',flush=True)
        self.ai_off();pending=self.call(f'/posts/{post["id"]}/comments',{'body':'Xin chào, cảm ơn bạn.'},alice,True)
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            if self.stats()['counts'].get('RETRY_WAIT',0):break
            time.sleep(.3)
        else:raise RuntimeError('No retry scheduled during outage')
        assert self.call(f'/comments/{pending["id"]}',token=alice)['visibility_status']=='PENDING_MODERATION'
        self.ai_on();assert self.wait('comment',pending,alice)['visibility_status']=='PUBLISHED'
        print('C PASS: real AI process stop/restart retained content and recovered',flush=True)
        target=create('Mời mọi người góp ý lịch sự.',post['id'],token=bob)
        first=create('Mày đúng là đồ ngu.',post['id'],target['id']);time.sleep(2)
        repeated=create('Mày đúng là đồ ngu.',post['id'],target['id'])
        ai=self.call(f'/moderation/content/comment/{repeated["id"]}',token=admin)['ai']
        assert_repeated_evidence(ai)
        queue=self.call('/moderation/queue?entity_type=comment',token=admin)['items']
        priority={item['content']['id']:item['priority'] for item in queue}
        assert priority[repeated['id']]<priority[first['id']]
        hidden=self.call('/moderation/decisions',{'entity_type':'comment','entity_id':repeated['id'],'action':'hide',
            'reason':'Synthetic demo review',**versions(repeated)},admin)
        appeal=self.call(f'/content/comment/{repeated["id"]}/appeals',{'reason':'Synthetic demo appeal',**versions(hidden)},alice)
        current=self.call(f'/content/comment/{repeated["id"]}/moderation',token=alice)['content']
        restored=self.call(f'/moderation/appeals/{appeal["id"]}/resolve',{'outcome':'RESTORED',
            'reason':'Synthetic appeal accepted',**versions(current)},admin)
        assert restored['content']['visibility_status']=='PUBLISHED' and restored['content']['review_status']=='RESOLVED'
        print('D PASS: repeated evidence, priority, manual hide, appeal and restore',flush=True)
        return {'status':'PASS','A':True,'B':True,'C':True,'D':True,'model':ai['model_version'],'threshold':ai['model_threshold'],
            'real_cpu_inference':True,'browser_automation':False,'synthetic_accounts_and_text_only':True,'live_db_used':False,
            'high_auto_hold_enabled':False}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--report',type=Path);args=parser.parse_args()
    if args.report and ROOT.parent not in args.report.resolve().parents:parser.error('Report must stay in workspace')
    record=None
    with tempfile.TemporaryDirectory(prefix='shieldvi-live-demo-') as folder:
        demo=Demo(folder)
        try:
            print('Starting REAL CPU model + worker + two UIs in an isolated demo...',flush=True);demo.start()
            if args.smoke:record=demo.smoke()
            else:
                print(f'\nSocial: {demo.social}\nAdmin: {demo.admin}')
                print('Accounts: demo_alice / demo_bob / demo_admin\nTemporary password:',demo.password)
                print('Commands: ai-off, ai-on, status, quit. No live DB touched.')
                while True:
                    command=input('demo> ').strip().lower()
                    if command in {'quit','q','exit'}:break
                    if command=='ai-off':demo.ai_off();print('AI stopped. Worker retains pending content and retries.')
                    elif command=='ai-on':demo.ai_on();print('AI ready. Exhausted jobs need staff Retry AI.')
                    elif command=='status':print(json.dumps(demo.stats(),indent=2))
                    else:print('Commands: ai-off, ai-on, status, quit')
        except (KeyboardInterrupt,EOFError):print('\nStopping demo...')
        finally:
            demo.close()
            if record:record['owned_processes_stopped']=all(proc.poll() is not None for proc in demo.owned)
    if record and args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if record:print(json.dumps(record,ensure_ascii=True))
    print('Demo stopped; temporary DB removed.')


if __name__=='__main__':main()
