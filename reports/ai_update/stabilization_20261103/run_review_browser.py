"""Serve existing blind UI on a disposable empty corpus; never submit labels."""
import json,os,socket,subprocess,sys,tempfile,time,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
base=R/'reports/ai_update/test_tmp';base.mkdir(parents=True,exist_ok=True)
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
with tempfile.TemporaryDirectory(prefix='stabilization-review-',dir=base) as directory:
    root=Path(directory).resolve();assert root.is_relative_to(base.resolve())
    code="import sys;from pathlib import Path;sys.path.insert(0,str(Path.cwd()/'scripts'));from real_dataset.review_app import create_app;import uvicorn;uvicorn.run(create_app(Path(sys.argv[1])),host='127.0.0.1',port=int(sys.argv[2]))"
    with (P/'review_server.log').open('w',encoding='utf-8') as log:
        proc=subprocess.Popen([sys.executable,'-X','utf8','-c',code,str(root),str(port)],cwd=R,stdout=log,stderr=subprocess.STDOUT,creationflags=flags)
        try:
            url='http://127.0.0.1:'+str(port)
            for _ in range(100):
                if proc.poll() is not None:raise RuntimeError('Owned UI server failed')
                try:
                    with urllib.request.urlopen(url+'/session',timeout=1) as response:
                        if response.status==200:break
                except OSError:time.sleep(.1)
            else:raise RuntimeError('UI server did not become ready')
            result=subprocess.run(['node',str(P/'review_browser.mjs'),url,str(P)],cwd=R,capture_output=True,text=True,encoding='utf-8',timeout=45,creationflags=flags)
            (P/'review_browser.log').write_text(result.stdout+result.stderr,encoding='utf-8')
            assert result.returncode==0,'Browser readiness check failed; see log'
        finally:
            proc.terminate()
            try:proc.wait(timeout=10)
            except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
(P/'review_cleanup.json').write_text(json.dumps({'owned_server_exited':proc.poll() is not None,'temporary_corpus_removed':not root.exists(),'actual_real_corpus_modified':False})+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','review_submissions':0,'human_gold_created':False}))
