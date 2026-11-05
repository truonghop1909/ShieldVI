"""Run local Chrome QA with isolated Social API/SQLite and synthetic accounts."""
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

WEB = Path(__file__).resolve().parents[1]
LEGACY = WEB.parents[1]
SERVICE = LEGACY / "services/social-api"
WORKSPACE = LEGACY.parent.resolve()
ARTIFACTS = (WORKSPACE / "ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T010").resolve()


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def ready(url, process):
    for _ in range(100):
        if process.poll() is not None:
            raise RuntimeError("Local QA server stopped; inspect server logs")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(.1)
    raise RuntimeError("Local QA server did not become ready")


def main():
    if WORKSPACE not in ARTIFACTS.parents:
        raise RuntimeError("QA artifacts must stay inside the workspace")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node is required")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    env = os.environ.copy()
    env.pop('FORCE_COLOR', None)
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1",
        SOCIAL_REGISTRATION_ENABLED="true", SOCIAL_AUTH_RATE_LIMIT="1000", SOCIAL_CONTENT_RATE_LIMIT="1000",
        VITE_REGISTRATION_ENABLED="true", VITE_SOCIAL_API_BASE="", SOCIAL_WEB_TEST_FIXTURES="1",
        SOCIAL_WEB_TEST_PASSWORD=secrets.token_urlsafe(24), PW_OUTPUT_DIR=str(ARTIFACTS / "browser"))
    api_port, web_port = port(), port()
    env["SOCIAL_API_PROXY_TARGET"] = f"http://127.0.0.1:{api_port}"
    env["SOCIAL_WEB_TEST_URL"] = f"http://127.0.0.1:{web_port}"
    owned = []
    with tempfile.TemporaryDirectory(prefix="shieldvi-T010-browser-") as temporary:
        env["SOCIAL_DATABASE_URL"] = "sqlite:///" + (Path(temporary) / "social-test.sqlite3").as_posix()
        for args, cwd in [(["-m", "alembic", "upgrade", "head"], SERVICE), ([str(WEB / "tests/seed_demo.py")], WEB)]:
            result = subprocess.run([sys.executable, *args], cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8")
            if result.returncode:
                raise RuntimeError(result.stderr)
        with (ARTIFACTS / "api-server.txt").open("w", encoding="utf-8") as api_log, (ARTIFACTS / "web-server.txt").open("w", encoding="utf-8") as web_log:
            try:
                api = subprocess.Popen([sys.executable, "-m", "uvicorn", "shieldvi_social.main:create_app", "--factory", "--app-dir", "src",
                    "--host", "127.0.0.1", "--port", str(api_port), "--no-proxy-headers"], cwd=SERVICE, env=env, stdout=api_log, stderr=subprocess.STDOUT, creationflags=flags)
                owned.append(api)
                ready(f"http://127.0.0.1:{api_port}/health", api)
                web = subprocess.Popen([node, str(WEB / "node_modules/vite/bin/vite.js"), "--host", "127.0.0.1", "--port", str(web_port), "--strictPort", "--configLoader", "runner"],
                    cwd=WEB, env=env, stdout=web_log, stderr=subprocess.STDOUT, creationflags=flags)
                owned.append(web)
                ready(env["SOCIAL_WEB_TEST_URL"], web)
                print("Temporary Social API and Social Web ready; Chrome QA starting", flush=True)
                result = subprocess.run([node, str(WEB / "node_modules/@playwright/test/cli.js"), "test"], cwd=WEB, env=env,
                    capture_output=True, text=True, encoding="utf-8", timeout=240, creationflags=flags)
                output = result.stdout + result.stderr
                (ARTIFACTS / "browser-tests.txt").write_text(output + f"\nEXIT_CODE={result.returncode}\n", encoding="utf-8")
                print(output, flush=True)
                return result.returncode
            finally:
                for process in reversed(owned):
                    if os.name == "nt" and process.poll() is None:
                        # Windows venv launchers can own a second Python process.
                        # Stop the exact owned tree before the launcher exits.
                        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, creationflags=flags)
                    elif process.poll() is None:
                        process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill(); process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
