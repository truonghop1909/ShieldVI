"""Bounded readiness and direct loopback HTTP, without AI training/model changes."""
import importlib.util,os,sys,secrets
from pathlib import Path
from types import SimpleNamespace
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from threading import Thread
import pytest

def module():
    spec=importlib.util.spec_from_file_location('demo_runner',Path(__file__).with_name('run_browser_actual.py'))
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

class Clock:
    def __init__(self):self.now=0
    def monotonic(self):return self.now
    def sleep(self,seconds):self.now+=seconds

def test_readiness_has_a_total_deadline_and_actionable_service_log(monkeypatch,capsys):
    value=module();clock=Clock();monkeypatch.setattr(value,'time',clock)
    def failed(*args,**kwargs):raise ConnectionRefusedError('Synthetic unavailable loopback')
    monkeypatch.setattr(value.LOCAL_HTTP,'open',failed)
    process=SimpleNamespace(poll=lambda:None,demo_service='Social API',demo_log='owned-demo/api.log')
    with pytest.raises(RuntimeError,match='Social API not ready within 1s.*owned-demo/api.log'):value.ready('http://127.0.0.1/health',process,1)
    assert clock.now<1.2 and 'Waiting for Social API' in capsys.readouterr().out

def test_exited_service_reports_exit_code_before_connecting():
    value=module();process=SimpleNamespace(poll=lambda:2,returncode=2,demo_service='Social API',demo_log='owned-demo/api.log')
    with pytest.raises(RuntimeError,match=r'Social API exited \(2\).*api.log'):value.ready('http://127.0.0.1/health',process)

def test_real_loopback_health_bypasses_environment_proxy(monkeypatch):
    monkeypatch.setenv('http_proxy','http://127.0.0.1:1');monkeypatch.setenv('HTTP_PROXY','http://127.0.0.1:1');monkeypatch.setenv('no_proxy','');monkeypatch.setenv('NO_PROXY','')
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):self.send_response(200);self.end_headers();self.wfile.write(b'{"status":"ready"}')
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        value=module();url=f'http://127.0.0.1:{server.server_port}/health'
        value.ready(url,SimpleNamespace(poll=lambda:None),2);assert value.call(url)=={'status':'ready'}
    finally:server.shutdown();server.server_close();thread.join(timeout=2)

def test_schema_setup_retains_actual_output_and_progress(tmp_path,capsys):
    value=module();owned=[];log=tmp_path/'schema.log'
    value.prepare('Test schema',[sys.executable,'-u','-c',"print('SCHEMA_READY')"],tmp_path,os.environ.copy(),log,owned,5)
    assert 'SCHEMA_READY' in log.read_text() and owned[0].returncode==0
    assert 'Test schema ready' in capsys.readouterr().out

def test_schema_failure_preserves_original_diagnostic(tmp_path):
    value=module();owned=[];log=tmp_path/'schema.log'
    with pytest.raises(RuntimeError,match=r'Test schema exited \(3\).*schema.log'):
        value.prepare('Test schema',[sys.executable,'-u','-c',"import sys;print('schema error',file=sys.stderr);sys.exit(3)"],tmp_path,os.environ.copy(),log,owned,5)
    assert 'schema error' in log.read_text() and owned[0].poll()==3

def test_stalled_schema_setup_times_out_and_stops_owned_process(tmp_path):
    value=module();owned=[];log=tmp_path/'schema.log'
    with pytest.raises(RuntimeError,match=r'Test schema not ready within 0.3s.*schema.log'):
        value.prepare('Test schema',[sys.executable,'-c','import time;time.sleep(30)'],tmp_path,os.environ.copy(),log,owned,.3)
    assert owned[0].poll() is not None

def test_operator_interrupt_during_schema_setup_stops_owned_process(tmp_path,monkeypatch):
    value=module();owned=[];log=tmp_path/'schema.log'
    def interrupt(_):raise KeyboardInterrupt
    monkeypatch.setattr(value.time,'sleep',interrupt)
    with pytest.raises(KeyboardInterrupt):
        value.prepare('Test schema',[sys.executable,'-c','import time;time.sleep(30)'],tmp_path,os.environ.copy(),log,owned,5)
    assert owned[0].poll() is not None

def test_default_demo_password_is_generated_per_run(monkeypatch):
    monkeypatch.delenv('SHIELDVI_DEMO_PASSWORD',raising=False);value=module()
    first=value.demo_password();second=value.demo_password()
    assert 12<=len(first)<=128 and first!=second

def test_operator_selected_demo_password_is_used_without_printing(monkeypatch,capsys):
    selected=secrets.token_urlsafe(18);monkeypatch.setenv('SHIELDVI_DEMO_PASSWORD',selected)
    assert module().demo_password()==selected and selected not in capsys.readouterr().out

@pytest.mark.parametrize('invalid',['','short',' '*12,'x'*129])
def test_invalid_demo_password_fails_before_account_creation(monkeypatch,invalid):
    monkeypatch.setenv('SHIELDVI_DEMO_PASSWORD',invalid)
    with pytest.raises(ValueError,match='12-128 characters'):module().demo_password()
