"""Real Chrome + both React apps + isolated Social API, synthetic local data."""
import json
import argparse
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

WEB=Path(__file__).resolve().parents[1]
ROOT=WEB.parents[1]
SOCIAL=ROOT / "apps/social-web"
SERVICE=ROOT / "services/social-api"
ARTIFACTS=ROOT.parent / "ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T013_T018"


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        return sock.getsockname()[1]


def ready(url,process):
    for _ in range(120):
        if process.poll() is not None:
            raise RuntimeError("QA server stopped; inspect logs")
        try:
            with urllib.request.urlopen(url,timeout=1) as response:
                if response.status==200:return
        except OSError:time.sleep(.1)
    raise RuntimeError("QA server did not become ready")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo",action="store_true",help="Keep disposable demo servers alive until Ctrl+C")
    options=parser.parse_args()
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    node=shutil.which("node")
    if not node:raise RuntimeError("Node required")
    flags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0
    env=os.environ.copy();env.pop("FORCE_COLOR",None)
    api_port,admin_port,social_port=port(),port(),port()
    env.update(PYTHONIOENCODING="utf-8",PYTHONDONTWRITEBYTECODE="1",SOCIAL_REGISTRATION_ENABLED="true",
        SOCIAL_AUTH_RATE_LIMIT="1000",SOCIAL_CONTENT_RATE_LIMIT="1000",VITE_SOCIAL_API_BASE="",
        MODERATION_WEB_TEST_FIXTURES="1",SOCIAL_WEB_TEST_PASSWORD=secrets.token_urlsafe(24),
        SOCIAL_API_PROXY_TARGET=f"http://127.0.0.1:{api_port}",MODERATION_WEB_TEST_URL=f"http://127.0.0.1:{admin_port}",
        SOCIAL_WEB_TEST_URL=f"http://127.0.0.1:{social_port}",PW_OUTPUT_DIR=str(ARTIFACTS / "browser"))
    owned=[];logs=[]
    with tempfile.TemporaryDirectory(prefix="shieldvi-T013-browser-") as temp:
        env["SOCIAL_DATABASE_URL"]="sqlite:///"+(Path(temp)/"social.sqlite3").as_posix()
        for args,cwd in [(["-m","alembic","upgrade","head"],SERVICE),([str(WEB/"tests/seed_demo.py")],WEB)]:
            result=subprocess.run([sys.executable,*args],cwd=cwd,env=env,capture_output=True,text=True,encoding="utf-8")
            if result.returncode:raise RuntimeError(result.stderr)
        try:
            commands=[("api",[sys.executable,"-m","uvicorn","shieldvi_social.main:create_app","--factory","--app-dir","src","--host","127.0.0.1","--port",str(api_port),"--no-proxy-headers"],SERVICE,f"http://127.0.0.1:{api_port}/health"),
                ("admin",[node,str(WEB/"node_modules/vite/bin/vite.js"),"--port",str(admin_port),"--strictPort","--configLoader","runner"],WEB,env["MODERATION_WEB_TEST_URL"]),
                ("social",[node,str(SOCIAL/"node_modules/vite/bin/vite.js"),"--port",str(social_port),"--strictPort","--configLoader","runner"],SOCIAL,env["SOCIAL_WEB_TEST_URL"])]
            for name,args,cwd,url in commands:
                log=(ARTIFACTS/f"{name}-server.txt").open("w",encoding="utf-8");logs.append(log)
                proc=subprocess.Popen(args,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=flags)
                owned.append(proc);ready(url,proc)
            with urllib.request.urlopen(f"http://127.0.0.1:{api_port}/openapi.json") as response:
                (ARTIFACTS / "social-review.openapi.json").write_bytes(response.read())
            if options.demo:
                print("Disposable synthetic demo; no real model inference. Ctrl+C stops servers and removes temporary DB.")
                print("Social:",env["SOCIAL_WEB_TEST_URL"],"Admin:",env["MODERATION_WEB_TEST_URL"])
                print("Accounts: fixture_author / fixture_viewer / fixture_mod / fixture_admin")
                print("Temporary demo password:",env["SOCIAL_WEB_TEST_PASSWORD"],flush=True)
                try:
                    while all(proc.poll() is None for proc in owned):
                        time.sleep(.5)
                except KeyboardInterrupt:
                    return 0
                raise RuntimeError("A demo server exited; inspect logs")
            result=subprocess.run([node,str(WEB/"node_modules/@playwright/test/cli.js"),"test"],cwd=WEB,env=env,
                capture_output=True,text=True,encoding="utf-8",timeout=300,creationflags=flags)
            output=result.stdout+result.stderr
            (ARTIFACTS/"browser-tests.txt").write_text(output+f"\nEXIT_CODE={result.returncode}\n",encoding="utf-8")
            print(output,flush=True)
            return result.returncode
        finally:
            for proc in reversed(owned):
                if proc.poll() is None:
                    if os.name=="nt":subprocess.run(["taskkill","/PID",str(proc.pid),"/T","/F"],capture_output=True,creationflags=flags)
                    else:proc.terminate()
                try:proc.wait(timeout=5)
                except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
            for log in logs:log.close()


if __name__=="__main__":raise SystemExit(main())
