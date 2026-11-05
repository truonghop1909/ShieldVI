"""Inject operator cancellation at first HTTP wait; verify real owned-process cleanup."""
import json,runpy,sys,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent
class InterruptedOpener:
    def open(self,*args,**kwargs):raise KeyboardInterrupt
urllib.request.build_opener=lambda *args,**kwargs:InterruptedOpener()
sys.argv=[str(P/'run_browser_actual.py'),'--interactive']
before={path for path in P.glob('demo_*') if path.is_dir()}
runpy.run_path(sys.argv[0],run_name='__main__')
created={path for path in P.glob('demo_*') if path.is_dir()}-before
assert len(created)==1
root=created.pop();cleanup=json.loads((root/'T043_cleanup.json').read_text())
assert cleanup['owned_processes_stopped'] and cleanup['owned_count']==3 # Two completed schema processes and Social API.
(P/'DEMO_STARTUP_FIX_interrupt.json').write_text(json.dumps({'status':'PASS','method':'injected KeyboardInterrupt at first HTTP readiness wait; real owned Social process cleaned up','root':str(root),'cleanup':cleanup,'training_started':False}),encoding='utf-8')
print('PASS: operator interruption handled without traceback; owned process stopped.')
