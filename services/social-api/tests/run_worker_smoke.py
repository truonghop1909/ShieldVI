"""Real HTTP/process smoke; synthetic AI scores and a disposable SQLite DB."""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid

SERVICE = Path(__file__).resolve().parents[1]
ROOT = SERVICE.parents[1]
WORKSPACE = ROOT.parent
ARTIFACTS = WORKSPACE / "ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T012_T017"


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        return sock.getsockname()[1]


def stop(process, flags):
    if process.poll() is None:
        if os.name=="nt":
            subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],capture_output=True,creationflags=flags)
        else:
            process.terminate()
    try: process.wait(timeout=5)
    except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)


def main():
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    token=secrets.token_urlsafe(32)
    env.update(PYTHONDONTWRITEBYTECODE="1",PYTHONIOENCODING="utf-8",SOCIAL_REGISTRATION_ENABLED="true",
        SOCIAL_AUTH_RATE_LIMIT="1000",SOCIAL_CONTENT_RATE_LIMIT="1000",SHIELDVI_SYNTHETIC_AI_FIXTURE="1",
        AI_SERVICE_TOKEN=token,SOCIAL_AI_SERVICE_TOKEN=token)
    flags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0
    owned=[]; lines=[]
    with tempfile.TemporaryDirectory(prefix="shieldvi-worker-smoke-") as temporary:
        env["SOCIAL_DATABASE_URL"]="sqlite:///"+(Path(temporary)/"social-smoke.sqlite3").as_posix()
        env["MODEL_PATH"]=str(Path(temporary)/"missing-real-checkpoint")
        api_port,ai_port=free_port(),free_port()
        env["SOCIAL_AI_BASE_URL"]=f"http://127.0.0.1:{ai_port}"
        def command(args,cwd=SERVICE):
            result=subprocess.run([sys.executable,*args],cwd=cwd,env=env,capture_output=True,text=True,encoding="utf-8",timeout=30,creationflags=flags)
            if result.returncode: raise RuntimeError(result.stderr)
            return result.stdout
        command(["-m","alembic","upgrade","head"])
        base=f"http://127.0.0.1:{api_port}"
        def call(method,path,payload=None,bearer=None,key=False):
            headers={"Content-Type":"application/json"}
            if bearer: headers["Authorization"]="Bearer "+bearer
            if key: headers["Idempotency-Key"]=str(uuid.uuid4())
            request=urllib.request.Request(base+path,method=method,headers=headers,data=json.dumps(payload).encode() if payload is not None else None)
            with urllib.request.urlopen(request,timeout=5) as response: return json.load(response)
        def wait_server(url,process):
            for _ in range(100):
                if process.poll() is not None: raise RuntimeError("Smoke server exited")
                try:
                    with urllib.request.urlopen(url,timeout=1) as response:
                        if response.status==200: return
                except OSError: time.sleep(.1)
            raise RuntimeError("Smoke server not ready")
        with (ARTIFACTS/"social-server.txt").open("w",encoding="utf-8") as social_log, (ARTIFACTS/"ai-fixture-server.txt").open("w",encoding="utf-8") as ai_log:
            try:
                social=subprocess.Popen([sys.executable,"-m","uvicorn","shieldvi_social.main:create_app","--factory","--app-dir","src","--host","127.0.0.1","--port",str(api_port),"--no-proxy-headers"],cwd=SERVICE,env=env,stdout=social_log,stderr=subprocess.STDOUT,creationflags=flags)
                owned.append(social); wait_server(base+"/health",social)
                password=secrets.token_urlsafe(24)
                call("POST","/api/v1/auth/register",{"username":"smoke_user","email":"smoke@example.com","password":password})
                bearer=call("POST","/api/v1/auth/login",{"username":"smoke_user","password":password})["access_token"]
                post=call("POST","/api/v1/posts",{"body":"Synthetic benign post"},bearer,True)
                comment=call("POST",f"/api/v1/posts/{post['id']}/comments",{"body":"Đm điện thoại hết pin"},bearer,True)
                command(["-m","shieldvi_social.worker","--once"])
                assert call("GET",f"/api/v1/posts/{post['id']}",bearer=bearer)["visibility_status"]=="PENDING_MODERATION"
                down=json.loads(command(["-m","shieldvi_social.worker","--stats"]))
                assert down["counts"].get("RETRY_WAIT")==1
                lines.append("AI down: queued content retained; one retry scheduled; nothing fail-open published")
                ai=subprocess.Popen([sys.executable,"-m","uvicorn","ai_fixture:app","--app-dir",str(SERVICE/"tests"),"--host","127.0.0.1","--port",str(ai_port),"--no-proxy-headers"],cwd=ROOT/"services/moderation-ai",env=env,stdout=ai_log,stderr=subprocess.STDOUT,creationflags=flags)
                owned.append(ai); wait_server(env["SOCIAL_AI_BASE_URL"]+"/health",ai)
                deadline=time.monotonic()+25
                while time.monotonic()<deadline:
                    command(["-m","shieldvi_social.worker","--once"])
                    stats=json.loads(command(["-m","shieldvi_social.worker","--stats"]))
                    if stats["counts"].get("SUCCEEDED")==2: break
                    time.sleep(.2)
                else: raise RuntimeError("Worker did not recover within smoke budget")
                assert call("GET",f"/api/v1/posts/{post['id']}",bearer=bearer)["visibility_status"]=="PUBLISHED"
                assert call("GET",f"/api/v1/comments/{comment['id']}",bearer=bearer)["visibility_status"]=="PUBLISHED_FLAGGED"
                assert call("GET","/api/v1/feed",bearer=bearer)["total"]==1
                lines.append("AI recovered via authenticated real HTTP adapter: benign -> PUBLISHED; profanity -> PUBLISHED_FLAGGED, never hidden")
                schema=call("GET","/openapi.json")
                (WORKSPACE/"ShieldVI_SocialAI_Design_Docs_v1/contracts/social-worker.openapi.json").write_text(json.dumps(schema,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                stop(ai,flags)
                pending=call("POST","/api/v1/posts",{"body":"Manual fallback fixture"},bearer,True)
                command(["-m","shieldvi_social.worker","--once"])
                staff=call("POST","/api/v1/auth/register",{"username":"smoke_staff","email":"staff@example.com","password":password})
                # Test-only role fixture in this disposable DB, never real provisioning.
                sys.path.insert(0,str(SERVICE/"src"))
                from shieldvi_social.config import Settings
                from shieldvi_social.db import make_engine,session_factory
                from shieldvi_social.models import User
                test_engine=make_engine(Settings(database_url=env["SOCIAL_DATABASE_URL"]))
                with session_factory(test_engine).begin() as db: db.get(User,staff["id"]).role="moderator"
                test_engine.dispose()
                staff_token=call("POST","/api/v1/auth/login",{"username":"smoke_staff","password":password})["access_token"]
                approved=call("POST","/api/v1/moderation/decisions",{"entity_type":"post","entity_id":pending["id"],"action":"approve","expected_revision":1,"expected_decision_version":0,"reason":"Synthetic offline manual review"},staff_token)
                assert approved["visibility_status"]=="PUBLISHED"
                command(["-m","shieldvi_social.worker","--once"])
                assert call("GET",f"/api/v1/posts/{pending['id']}",bearer=bearer)["decision_version"]==1
                lines.append("AI offline again: moderator HTTP approval succeeds without model; subsequent worker cannot overwrite it")
                lines.append("Synthetic predictor only; no real checkpoint loaded; temporary DB/accounts only; EXIT_CODE=0")
            finally:
                for process in reversed(owned): stop(process,flags)
    (ARTIFACTS/"live-http-smoke.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("\n".join(lines))


if __name__=="__main__": main()
