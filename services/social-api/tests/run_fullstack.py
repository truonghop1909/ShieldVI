"""Five-process E2E: AI, Social API, worker, Social Web, Moderation Web.

Only synthetic accounts and a disposable DB; never deploys or loads checkpoint.
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

SERVICE=Path(__file__).resolve().parents[1]
ROOT=SERVICE.parents[1]
SOCIAL=ROOT/'apps/social-web'
ADMIN=ROOT/'apps/moderation-web'
ARTIFACTS=ROOT.parent/'ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T014_T019/fullstack'


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));return sock.getsockname()[1]


def ready(url,process):
    for _ in range(150):
        if process.poll() is not None:raise RuntimeError('E2E server exited; inspect logs')
        try:
            with urllib.request.urlopen(url,timeout=1) as response:
                if response.status==200:return
        except OSError:time.sleep(.1)
    raise RuntimeError('E2E server did not become ready')


def stop(proc,flags):
    if proc.poll() is None:
        if os.name=='nt':subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,creationflags=flags)
        else:proc.terminate()
    try:proc.wait(timeout=5)
    except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    node=shutil.which('node')
    if not node:raise RuntimeError('Node required')
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    ports=[port() for _ in range(4)]
    api_port,ai_port,social_port,admin_port=ports
    env=os.environ.copy();env.pop('FORCE_COLOR',None)
    token=secrets.token_urlsafe(32)
    env.update(PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',SHIELDVI_FULLSTACK_E2E='1',
        MODERATION_WEB_TEST_FIXTURES='1',SOCIAL_WEB_TEST_PASSWORD=secrets.token_urlsafe(24),
        SOCIAL_REGISTRATION_ENABLED='true',VITE_REGISTRATION_ENABLED='true',SOCIAL_AUTH_RATE_LIMIT='1000',
        SOCIAL_CONTENT_RATE_LIMIT='1000',VITE_SOCIAL_API_BASE='',SOCIAL_AI_SERVICE_TOKEN=token,AI_SERVICE_TOKEN=token,
        SOCIAL_WORKER_POLL_SECONDS='.1',SOCIAL_WORKER_MAX_ATTEMPTS='3',AI_SERVICE_RATE_LIMIT='1000',
        SOCIAL_API_PROXY_TARGET=f'http://127.0.0.1:{api_port}',SOCIAL_AI_BASE_URL=f'http://127.0.0.1:{ai_port}',
        SOCIAL_WEB_TEST_URL=f'http://127.0.0.1:{social_port}',MODERATION_WEB_TEST_URL=f'http://127.0.0.1:{admin_port}',
        PW_OUTPUT_DIR=str(ARTIFACTS/'browser'),SHIELDVI_E2E_METRICS=str(ARTIFACTS/'metrics.json'),
        SHIELDVI_TEST_PYTHON=sys.executable,SHIELDVI_TEST_SERVICE=str(SERVICE),STORE_SUMMARIES='0')
    owned=[];logs=[]
    try:
        with tempfile.TemporaryDirectory(prefix='shieldvi-T014-e2e-') as temp:
            temporary=Path(temp)
            env.update(SOCIAL_DATABASE_URL='sqlite:///'+(temporary/'social.sqlite3').as_posix(),
                MODEL_PATH=str(temporary/'nonexistent-checkpoint'),REVIEW_DB_PATH=str(temporary/'ai-review.sqlite3'),
                DB_PATH=str(temporary/'ai-summary.sqlite3'),SHIELDVI_AI_FAULT_FILE=str(temporary/'fault.json'))
            (temporary/'fault.json').write_text(json.dumps({'mode':'normal'}),encoding='utf-8')
            def command(args,cwd):
                result=subprocess.run([sys.executable,*args],cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=30,creationflags=flags)
                if result.returncode:raise RuntimeError(result.stderr)
            command(['-m','alembic','upgrade','head'],SERVICE)
            command([str(ADMIN/'tests/seed_demo.py')],ROOT)
            commands=[('social-api',[sys.executable,'-m','uvicorn','shieldvi_social.main:create_app','--factory','--app-dir','src','--host','127.0.0.1','--port',str(api_port),'--no-proxy-headers'],SERVICE,env['SOCIAL_API_PROXY_TARGET']+'/health'),
                ('ai-fixture',[sys.executable,'-m','uvicorn','fullstack_ai:app','--app-dir',str(SERVICE/'tests'),'--host','127.0.0.1','--port',str(ai_port),'--no-proxy-headers'],ROOT/'services/moderation-ai',env['SOCIAL_AI_BASE_URL']+'/health'),
                ('social-web',[node,str(SOCIAL/'node_modules/vite/bin/vite.js'),'--port',str(social_port),'--strictPort','--configLoader','runner'],SOCIAL,env['SOCIAL_WEB_TEST_URL']),
                ('moderation-web',[node,str(ADMIN/'node_modules/vite/bin/vite.js'),'--port',str(admin_port),'--strictPort','--configLoader','runner'],ADMIN,env['MODERATION_WEB_TEST_URL']),
                ('worker',[sys.executable,'-m','shieldvi_social.worker'],SERVICE,None)]
            try:
                for name,args,cwd,url in commands:
                    log=(ARTIFACTS/f'{name}.txt').open('w',encoding='utf-8');logs.append(log)
                    process=subprocess.Popen(args,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=flags)
                    owned.append(process)
                    if url:ready(url,process)
                result=subprocess.run([node,str(ADMIN/'node_modules/@playwright/test/cli.js'),'test'],cwd=ADMIN,env=env,
                    capture_output=True,text=True,encoding='utf-8',timeout=240,creationflags=flags)
                output=result.stdout+result.stderr
                for secret in (token,env['SOCIAL_WEB_TEST_PASSWORD']):output=output.replace(secret,'[REDACTED_TEST_SECRET]')
                # Playwright failure contexts may include even password input values.
                # Keep diagnostics useful without retaining temporary credentials.
                for diagnostic in (ARTIFACTS/'browser').rglob('*.md'):
                    content=diagnostic.read_text(encoding='utf-8')
                    for secret in (token,env['SOCIAL_WEB_TEST_PASSWORD']):content=content.replace(secret,'[REDACTED_TEST_SECRET]')
                    diagnostic.write_text(content,encoding='utf-8')
                (ARTIFACTS/'browser-tests.txt').write_text(output+f'\nEXIT_CODE={result.returncode}\n',encoding='utf-8')
                # Check real server logs, not only captured unit-test logging.
                sensitive=[token,env['SOCIAL_WEB_TEST_PASSWORD'],'E2E_PRIVATE_CONTENT_019','E2E_PRIVATE_EMAIL_019@example.com']
                for log in logs:log.flush()
                leaks=[]
                for log_path in (path for path in ARTIFACTS.glob('*.txt') if path.name!='browser-tests.txt'):
                    content=log_path.read_text(encoding='utf-8')
                    if any(marker in content for marker in sensitive):leaks.append(log_path.name)
                (ARTIFACTS/'log-privacy.json').write_text(json.dumps({'checked_server_files':len(logs),
                    'sensitive_markers_found_in':leaks,'synthetic_markers_only':True},indent=2)+'\n',encoding='utf-8')
                print(output,flush=True)
                if leaks:raise RuntimeError('Sensitive synthetic marker appeared in logs')
                alive={name:proc.poll() is None for (name,*_),proc in zip(commands,owned)}
                (ARTIFACTS/'process-health.json').write_text(json.dumps(alive,indent=2)+'\n',encoding='utf-8')
                if not all(alive.values()):raise RuntimeError('An E2E process stopped unexpectedly, inspect logs')
                return result.returncode
            finally:
                for process in reversed(owned):stop(process,flags)
                for log in logs:log.close()
    finally:
        (ARTIFACTS/'cleanup.json').write_text(json.dumps({'owned_processes_exited':all(proc.poll() is not None for proc in owned),
            'temporary_db_only':True,'live_db_migrated':False})+'\n',encoding='utf-8')


if __name__=='__main__':raise SystemExit(main())
