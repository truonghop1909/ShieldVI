"""Owned four-process local E2E with temporary SQLite and synthetic accounts."""
import contextlib,json,os,secrets,shutil,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;SERVICE=R/'services/social-api';WEB=R/'apps/social-web'
LOCAL_HTTP=urllib.request.build_opener(urllib.request.ProxyHandler({}))

def progress(message):print(message,flush=True)

def demo_password():
    selected=os.environ.get('SHIELDVI_DEMO_PASSWORD')
    if selected is None:return secrets.token_urlsafe(24)
    if not 12<=len(selected)<=128 or not selected.strip():
        raise ValueError('Demo password must contain 12-128 characters and cannot be blank.')
    return selected

def stop_process(process):
    if process.poll() is None:
        if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        else:process.terminate()
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)

def prepare(name,args,cwd,env,log_path,owned,timeout_seconds=90):
    """Bound schema setup with live diagnostics and cleanup on cancellation."""
    started=time.monotonic();notice=started;deadline=started+timeout_seconds
    progress(f'Starting {name}. Log: {log_path}')
    with Path(log_path).open('w',encoding='utf-8') as log:
        process=subprocess.Popen(args,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        owned.append(process)
        try:
            while process.poll() is None:
                current=time.monotonic()
                if current>=deadline:raise RuntimeError(f'{name} not ready within {timeout_seconds}s. Log: {log_path}')
                if current>=notice:
                    progress(f'Waiting for {name}: {current-started:.0f}s / {timeout_seconds}s. Log: {log_path}');notice=current+5
                time.sleep(min(.1,max(.001,deadline-current)))
            if process.returncode:raise RuntimeError(f'{name} exited ({process.returncode}). Log: {log_path}')
            progress(f'{name} ready ({time.monotonic()-started:.1f}s).')
        finally:stop_process(process)

def port():
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
def ready(url,process,timeout_seconds=90):
    service=getattr(process,'demo_service','Local service');log=getattr(process,'demo_log','service log')
    started=time.monotonic();deadline=started+timeout_seconds;notice=started
    while time.monotonic()<deadline:
        if process.poll() is not None:raise RuntimeError(f'{service} exited ({process.returncode}). Log: {log}')
        current=time.monotonic()
        if current>=notice:
            progress(f'Waiting for {service}: {current-started:.0f}s / {timeout_seconds}s. Log: {log}');notice=current+5
        try:
            with LOCAL_HTTP.open(url,timeout=min(.5,max(.01,deadline-current))) as response:
                if response.status==200:
                    progress(f'{service} ready ({time.monotonic()-started:.1f}s).');return
        except OSError:time.sleep(.1)
    raise RuntimeError(f'{service} not ready within {timeout_seconds}s. Log: {log}')
def call(url,payload=None,headers=None):
    request=urllib.request.Request(url,data=json.dumps(payload).encode() if payload is not None else None,
        headers={'Content-Type':'application/json',**(headers or {})},method='POST' if payload is not None else 'GET')
    with LOCAL_HTTP.open(request,timeout=15) as response:return json.loads(response.read())

if __name__=='__main__':
    feed_check='--feed-check' in sys.argv
    studio_check='--studio-check' in sys.argv
    responsive_check=any(flag in sys.argv for flag in ('--responsive-before','--responsive-check'))
    visual_mode='before' if '--visual-audit' in sys.argv else 'after' if '--visual-check' in sys.argv else ''
    interactive_check='--interactive-check' in sys.argv or feed_check or studio_check
    interactive='--interactive' in sys.argv or interactive_check or bool(visual_mode)
    progress('Starting isolated ShieldVI demo. Keep this window open; Ctrl+C stops the demo.')
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0;owned=[];logs=[];node=shutil.which('node');assert node
    password=demo_password();key=secrets.token_urlsafe(32);ports=[]
    while len(ports)<4:
        number=port()
        if number not in ports:ports.append(number)
    api_port,ai_port,web_port,admin_port=ports;api_url=f'http://127.0.0.1:{api_port}';ai_url=f'http://127.0.0.1:{ai_port}';web_url=f'http://127.0.0.1:{web_port}'
    env=os.environ.copy();env.update(PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',SHIELDVI_LIVE_E2E='1',
        PYTHONPATH=os.pathsep.join([str(SERVICE/'src'),str(R/'services/moderation-ai'),str(R/'scripts')]),SOCIAL_REGISTRATION_ENABLED='true',
        SOCIAL_AUTH_RATE_LIMIT='1000',SOCIAL_CONTENT_RATE_LIMIT='1000',SOCIAL_AI_SERVICE_TOKEN=key,AI_SERVICE_TOKEN=key,
        AI_SERVICE_RATE_LIMIT='1000',SOCIAL_AI_BASE_URL=ai_url,SOCIAL_WORKER_POLL_SECONDS='.1',SOCIAL_AI_READ_TIMEOUT='5',
        SOCIAL_API_PROXY_TARGET=api_url,VITE_SOCIAL_API_BASE='',LIVE_TEST_WEB=web_url,LIVE_TEST_AI=ai_url,LIVE_TEST_PASSWORD=password,LIVE_TEST_ARTIFACTS=str(P))
    env.pop('MODEL_PATH',None);env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='-1',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',TOKENIZERS_PARALLELISM='false',STORE_SUMMARIES='0')
    log_root=P
    def launch(name,args,cwd):
        log=(log_root/(name+'.log')).open('w',encoding='utf-8');logs.append(log)
        services={'T043_api':'Social API','T043_ai_actual':'Moderation AI','T043_web':'Social Web','T043_admin_web':'Moderator Web'}
        progress('Starting '+services.get(name,name)+'...')
        process=subprocess.Popen(args,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=flags)
        process.demo_service=services.get(name,name);process.demo_log=str(log_root/(name+'.log'));owned.append(process);return process
    class KeptDirectory:
        def __init__(self):
            path=P/('demo_'+secrets.token_hex(8));path.mkdir();self.name=str(path)
        def cleanup(self):pass
    # Every check gets retained unique evidence; never overwrite old handoff logs.
    temporary_directory=KeptDirectory()
    try:
        with contextlib.nullcontext(temporary_directory.name) as temporary:
            temp=Path(temporary).resolve();assert temp.is_relative_to(P.resolve())
            progress('Demo data/log directory: '+str(temp))
            log_root=temp;env['LIVE_TEST_ARTIFACTS']=str(temp)
            if interactive:
                log_root=temp;env['SHIELDVI_DEMO_ROOT']=str(temp);env['SHIELDVI_DEMO_BROWSER_HEADLESS']='1' if interactive_check else '0'
                env['SHIELDVI_DEMO_VISUAL_MODE']=visual_mode
                env['SHIELDVI_DEMO_FEED_CHECK']='1' if feed_check else '0'
                env['SHIELDVI_DEMO_STUDIO_CHECK']='1' if studio_check else '0'
                env['LIVE_TEST_ARTIFACTS']=str(temp)
            env['SHIELDVI_LIVE_SQL_TIMINGS']=str(temp/'sql_timing.jsonl')
            db_path=temp/'social.sqlite3';env['SOCIAL_DATABASE_URL']='sqlite:///'+db_path.as_posix()
            progress('Preparing the new demo database...')
            for name,args in (('Base schema',['-m','alembic','upgrade','head']),('Live schema',['-m','shieldvi_social.live_schema','--database-url',env['SOCIAL_DATABASE_URL']])):
                prepare(name,[sys.executable,'-u',*args],SERVICE,env,log_root/('T043_'+name.lower().replace(' ','_')+'.log'),owned)
            if interactive or responsive_check:
                progress('Checking Studio data/model manifests (read-only). This may take a moment...')
                sys.path.insert(0,str(R/'scripts'))
                from ml_studio.datasets import DatasetStore
                from ml_studio.evaluation import EvaluationJobs
                studio=DatasetStore.initialize(temp/'studio')
                registry_status=EvaluationJobs(studio).initialize(allow_missing_baseline=True)
                env['SHIELDVI_DEMO_V1_UNAVAILABLE']='0' if registry_status['evaluation_enabled'] else '1'
                (temp/'studio_registry_status.json').write_text(json.dumps(registry_status),encoding='utf-8')
                if not registry_status['evaluation_enabled']:
                    progress('Original V1 baseline unavailable: comparison/rollback disabled. Realtime AI keeps the existing V1.1 default (0.41); no model substitution.')
                env['SHIELDVI_STUDIO_ROOT']=str(studio.root)
                env['PYTHONPATH']=os.pathsep.join([str(R/'scripts'),env['PYTHONPATH']])
            api=launch('T043_api',[sys.executable,'-m','uvicorn','shieldvi_social.live_app:create_app','--factory','--host','127.0.0.1','--port',str(api_port),'--loop','demo_loop:new_event_loop','--no-access-log'],SERVICE)
            ready(api_url+'/health',api)
            accounts={}
            for username in ('live_alice','live_bob','live_carol','live_dave','live_emma','live_admin'):
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
            ai_args=[str(R/'.venv/Scripts/python.exe'),'-m','uvicorn','app.live_entrypoint:create_app','--factory','--app-dir',str(R/'services/moderation-ai'),'--host','127.0.0.1','--port',str(ai_port),'--no-access-log']
            ai=launch('T043_ai_actual',ai_args,R);ready(ai_url+'/health',ai)
            health=call(ai_url+'/health')
            if not health.get('model_loaded'):raise RuntimeError('Moderation AI checkpoint is unavailable. Log: '+str(log_root/'T043_ai_actual.log'))
            (log_root/'T043_actual_health.json').write_text(json.dumps(health),encoding='utf-8')
            worker=launch('T043_worker',[sys.executable,'-m','shieldvi_social.live_worker','--incremental'],SERVICE)
            headers={'Authorization':'Bearer '+accounts['live_alice'],'Idempotency-Key':str(__import__('uuid').uuid4())}
            thread=call(api_url+'/api/v1/posts',{'body':'Synthetic realtime fixture — public conversation'},headers);env['LIVE_TEST_THREAD']=thread['id']
            for _ in range(100):
                value=call(api_url+'/api/v1/posts/'+thread['id'],headers=headers)
                if value['visibility_status']=='PUBLISHED':break
                if worker.poll() is not None:raise RuntimeError('Owned worker exited')
                time.sleep(.1)
            else:raise RuntimeError('Fixture thread not published')
            web=launch('T043_web',[node,str(WEB/'node_modules/vite/bin/vite.js'),'--config','vite.live.config.js','--configLoader','runner','--host','127.0.0.1','--port',str(web_port),'--strictPort'],WEB);ready(web_url+'/live.html',web)
            admin_web=R/'apps/moderation-web'
            admin=launch('T043_admin_web',[node,str(admin_web/'node_modules/vite/bin/vite.js'),'--config','vite.live.config.js','--configLoader','runner','--host','127.0.0.1','--port',str(admin_port),'--strictPort'],admin_web)
            env['LIVE_TEST_ADMIN']=f'http://127.0.0.1:{admin_port}';ready(env['LIVE_TEST_ADMIN']+'/live.html',admin)
            if interactive:
                for module in ('training','evaluation'):
                    launch('demo_'+module,[str(R/'.venv/Scripts/python.exe'),'-m','ml_studio.'+module,'--root',env['SHIELDVI_STUDIO_ROOT']],R)
                opened=launch('demo_browsers',[node,str(R/'scripts/demo_open_browsers.mjs')],R)
                progress('Downloaded exports are retained in: '+str(temp/'downloads'))
                pointer={'root':str(temp),'running':True,'pid':os.getpid(),'urls':{'social':web_url+'/live.html?thread='+thread['id'],'moderator':env['LIVE_TEST_ADMIN']+'/live.html','studio':env['LIVE_TEST_ADMIN']+'/studio.html'}}
                (P/'ACTIVE_DEMO.json').write_text(json.dumps(pointer),encoding='utf-8')
                print(json.dumps({'status':'DEMO_READY','root':str(temp),'urls':pointer['urls'],'credentials':'filled in isolated browser contexts; not logged','training':'idle until operator starts eligible CPU job'}),flush=True)
                while not (temp/'stop.request').exists() and opened.poll() is None:
                    if feed_check and (temp/'ai_pause.request').exists() and not (temp/'ai_paused.json').exists():
                        stop_process(ai);(temp/'ai_paused.json').write_text(json.dumps({'owned_ai_stopped':ai.poll() is not None}),encoding='utf-8')
                    if feed_check and (temp/'ai_resume.request').exists() and not (temp/'ai_resumed.json').exists():
                        ai=launch('T043_ai_recovered',ai_args,R);ready(ai_url+'/health',ai)
                        recovered=call(ai_url+'/health');assert recovered.get('model_loaded') and recovered.get('model_name')==health.get('model_name')
                        (temp/'ai_resumed.json').write_text(json.dumps({'actual_health':recovered,'default_unchanged':True}),encoding='utf-8')
                    if interactive_check and (temp/'browser_smoke.json').exists():
                        stop_result=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(R/'scripts/demo_realtime_stop.ps1')],capture_output=True,text=True,creationflags=flags)
                        assert stop_result.returncode==0 and (temp/'stop.request').exists()
                        evidence=json.loads((temp/'browser_smoke.json').read_text());evidence.update(stop_script_pass=True,root=str(temp),actual_ai_health=health,retained_data=True)
                        (temp/'interactive_check.json').write_text(json.dumps(evidence),encoding='utf-8');print(json.dumps({'status':'PASS','interactive_contexts':evidence['contexts'],'stop_script':True,'no_training':True}),flush=True)
                    time.sleep(.5)
                if opened.poll() is not None and opened.returncode!=0:raise RuntimeError('Demo browser setup failed. Log: '+str(temp/'demo_browsers.log'))
                exit(0)
            if '--comment-button-check' in sys.argv:env['LIVE_TEST_COMMENT_BUTTON_CHECK']='1'
            browser_script='browser_comment_ux_20261105.mjs' if any(flag in sys.argv for flag in ('--comment-ux-check','--comment-button-check')) else 'browser_t043.mjs'
            if '--identity-check' in sys.argv:browser_script='browser_reply_identity_20261105.mjs'
            if '--quick-json-check' in sys.argv:browser_script='browser_quick_json_20261105.mjs'
            if '--native-download-check' in sys.argv:browser_script='browser_native_json_download_20261105.mjs'
            if responsive_check:
                browser_script='browser_responsive_20261105.mjs'
                env['SHIELDVI_RESPONSIVE_BEFORE']='1' if '--responsive-before' in sys.argv else '0'
            if '--responsive-regression' in sys.argv:browser_script='browser_responsive_regression_20261105.mjs'
            result=subprocess.run([node,str(P/browser_script)],cwd=R,env=env,capture_output=True,text=True,encoding='utf-8',timeout=360 if responsive_check or '--responsive-regression' in sys.argv else 180,creationflags=flags)
            output=(result.stdout+result.stderr).replace(password,'[REDACTED]').replace(key,'[REDACTED]')
            (log_root/'T043_browser.log').write_text(output+f'\nEXIT_CODE={result.returncode}\n',encoding='utf-8');print(output,flush=True)
            if result.returncode:raise RuntimeError('Browser checks failed; see redacted T043_browser.log')
            from shieldvi_social.models import ModerationResult
            from shieldvi_social.live_store import LiveEvent
            engine=make_engine(Settings(database_url=env['SOCIAL_DATABASE_URL']))
            with session_factory(engine)() as db:
                results=[json.loads(r.signals_json) for r in db.scalars(select(ModerationResult))]
                events=[dict(id=r.id,content_id=r.content_id,status=r.analysis_status,created_ms=r.created_ms,event_type=r.event_type) for r in db.scalars(select(LiveEvent))]
            engine.dispose()
            assert results and all(r['model_threshold']==.41 and 'FIXTURE' not in r['model_version'] and r['conversation_signals']['processor']=='default-v5' for r in results)
            (log_root/'T043_actual_results.json').write_text(json.dumps({'results':results,'events':events,'sql_enqueue_timings':[json.loads(line) for line in (temp/'sql_timing.jsonl').read_text(encoding='utf-8').splitlines()],'neural_inference':True,'default_unchanged':True}),encoding='utf-8')
    except KeyboardInterrupt:
        progress('\nCtrl+C received. Stopping only this demo\'s processes...')
    finally:
        for process in reversed(owned):stop_process(process)
        for log in logs:log.close()
        temporary_directory.cleanup()
        if interactive and (P/'ACTIVE_DEMO.json').exists():
            pointer=json.loads((P/'ACTIVE_DEMO.json').read_text(encoding='utf-8'))
            if pointer['root']==temporary_directory.name:
                pointer['running']=False;(P/'ACTIVE_DEMO.json').write_text(json.dumps(pointer),encoding='utf-8')
        (log_root/'T043_cleanup.json').write_text(json.dumps({'owned_processes_stopped':all(p.poll() is not None for p in owned),'owned_count':len(owned),'temporary_db_only':True,'production_changed':False}),encoding='utf-8')
        if interactive:progress('Demo stopped. Data/logs retained at: '+temporary_directory.name)
