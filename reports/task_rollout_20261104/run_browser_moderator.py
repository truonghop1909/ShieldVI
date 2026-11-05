"""Owned four-process local E2E with temporary SQLite and synthetic accounts."""
import contextlib,json,os,secrets,shutil,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;SERVICE=R/'services/social-api';WEB=R/'apps/social-web'

def port():
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
def ready(url,process):
    for _ in range(150):
        if process.poll() is not None:raise RuntimeError('Owned test server exited')
        try:
            with urllib.request.urlopen(url,timeout=1) as response:
                if response.status==200:return
        except OSError:time.sleep(.1)
    raise RuntimeError('Owned test server readiness timed out')
def call(url,payload=None,headers=None):
    request=urllib.request.Request(url,data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Content-Type':'application/json',**(headers or {})},method='POST' if payload is not None else 'GET')
    with urllib.request.urlopen(request,timeout=15) as response:return json.loads(response.read())

if __name__=='__main__':
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0;owned=[];logs=[];node=shutil.which('node');assert node
    password=secrets.token_urlsafe(24);key=secrets.token_urlsafe(32);ports=[]
    while len(ports)<4:
        number=port()
        if number not in ports:ports.append(number)
    api_port,ai_port,web_port,admin_port=ports;api_url=f'http://127.0.0.1:{api_port}';ai_url=f'http://127.0.0.1:{ai_port}';web_url=f'http://127.0.0.1:{web_port}'
    env=os.environ.copy();env.update(PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',SHIELDVI_LIVE_E2E='1',
        PYTHONPATH=os.pathsep.join([str(SERVICE/'src'),str(R/'services/moderation-ai')]),SOCIAL_REGISTRATION_ENABLED='true',
        SOCIAL_AUTH_RATE_LIMIT='1000',SOCIAL_CONTENT_RATE_LIMIT='1000',SOCIAL_AI_SERVICE_TOKEN=key,AI_SERVICE_TOKEN=key,
        AI_SERVICE_RATE_LIMIT='1000',SOCIAL_AI_BASE_URL=ai_url,SOCIAL_WORKER_POLL_SECONDS='.1',SOCIAL_AI_READ_TIMEOUT='5',
        SOCIAL_API_PROXY_TARGET=api_url,VITE_SOCIAL_API_BASE='',LIVE_TEST_WEB=web_url,LIVE_TEST_AI=ai_url,LIVE_TEST_PASSWORD=password,LIVE_TEST_ARTIFACTS=str(P))
    def launch(name,args,cwd):
        log=(P/(name+'.log')).open('w',encoding='utf-8');logs.append(log)
        process=subprocess.Popen(args,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=flags);owned.append(process);return process
    temporary_directory=tempfile.TemporaryDirectory(prefix='live-e2e-',dir=str(P))
    try:
        with contextlib.nullcontext(temporary_directory.name) as temporary:
            temp=Path(temporary).resolve();assert temp.is_relative_to(P.resolve())
            db_path=temp/'social.sqlite3';env['SOCIAL_DATABASE_URL']='sqlite:///'+db_path.as_posix()
            for args in (['-m','alembic','upgrade','head'],['-m','shieldvi_social.live_schema','--database-url',env['SOCIAL_DATABASE_URL']]):
                result=subprocess.run([sys.executable,*args],cwd=SERVICE,env=env,capture_output=True,text=True,encoding='utf-8',creationflags=flags)
                if result.returncode:raise RuntimeError('Isolated schema initialization failed: '+result.stderr)
            api=launch('T038_api',[sys.executable,'-m','uvicorn','shieldvi_social.live_app:create_app','--factory','--host','127.0.0.1','--port',str(api_port),'--no-access-log'],SERVICE)
            ready(api_url+'/health',api)
            accounts={}
            for username in ('live_alice','live_bob','live_admin'):
                call(api_url+'/api/v1/auth/register',{'username':username,'email':username+'@example.org','password':password})
                accounts[username]=call(api_url+'/api/v1/auth/login',{'username':username,'password':password})['access_token']
            # Synthetic demo admin bootstrap in this owned temporary DB only.
            sys.path.insert(0,str(SERVICE/'src'))
            from shieldvi_social.config import Settings
            from shieldvi_social.db import make_engine,session_factory
            from shieldvi_social.models import User
            from sqlalchemy import select
            engine=make_engine(Settings(database_url=env['SOCIAL_DATABASE_URL']))
            with session_factory(engine).begin() as db:db.scalar(select(User).where(User.username=='live_admin')).role='admin'
            engine.dispose()
            ai=launch('T038_ai_fixture',[sys.executable,'-m','uvicorn','fixture_live_ai:app','--app-dir',str(P),'--host','127.0.0.1','--port',str(ai_port),'--no-access-log'],R);ready(ai_url+'/health',ai)
            worker=launch('T038_worker',[sys.executable,'-m','shieldvi_social.live_worker','--incremental'],SERVICE)
            headers={'Authorization':'Bearer '+accounts['live_alice'],'Idempotency-Key':str(__import__('uuid').uuid4())}
            thread=call(api_url+'/api/v1/posts',{'body':'Synthetic realtime fixture — public conversation'},headers);env['LIVE_TEST_THREAD']=thread['id']
            for _ in range(100):
                value=call(api_url+'/api/v1/posts/'+thread['id'],headers=headers)
                if value['visibility_status']=='PUBLISHED':break
                if worker.poll() is not None:raise RuntimeError('Owned worker exited')
                time.sleep(.1)
            else:raise RuntimeError('Fixture thread not published')
            web=launch('T038_web',[node,str(WEB/'node_modules/vite/bin/vite.js'),'--config','vite.live.config.js','--configLoader','runner','--host','127.0.0.1','--port',str(web_port),'--strictPort'],WEB);ready(web_url+'/live.html',web)
            admin_web=R/'apps/moderation-web'
            admin=launch('T038_admin_web',[node,str(admin_web/'node_modules/vite/bin/vite.js'),'--config','vite.live.config.js','--configLoader','runner','--host','127.0.0.1','--port',str(admin_port),'--strictPort'],admin_web)
            env['LIVE_TEST_ADMIN']=f'http://127.0.0.1:{admin_port}';ready(env['LIVE_TEST_ADMIN']+'/live.html',admin)
            result=subprocess.run([node,str(P/'browser_t038.mjs')],cwd=R,env=env,capture_output=True,text=True,encoding='utf-8',timeout=180,creationflags=flags)
            output=(result.stdout+result.stderr).replace(password,'[REDACTED]').replace(key,'[REDACTED]')
            (P/'T038_browser.log').write_text(output+f'\nEXIT_CODE={result.returncode}\n',encoding='utf-8');print(output,flush=True)
            if result.returncode:raise RuntimeError('Browser checks failed; see redacted T038_browser.log')
    finally:
        for process in reversed(owned):
            if process.poll() is None:
                if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,creationflags=flags)
                else:process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
        for log in logs:log.close()
        temporary_directory.cleanup()
        (P/'T038_cleanup.json').write_text(json.dumps({'owned_processes_stopped':all(p.poll() is not None for p in owned),'owned_count':len(owned),'temporary_db_only':True,'production_changed':False}),encoding='utf-8')
