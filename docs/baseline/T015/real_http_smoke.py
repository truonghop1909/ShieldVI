"""Compare rollback-source and canonical AI over HTTP with the same real CPU model.

All review/summary writes go to disposable databases, never the project DBs.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]/'ShieldVI_V3_Hybrid_Review'
AI=ROOT/'services/moderation-ai'


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));return sock.getsockname()[1]


def stop(process,flags):
    if process.poll() is None:
        if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,creationflags=flags)
        else:process.terminate()
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    token=secrets.token_urlsafe(32);runs={}
    with tempfile.TemporaryDirectory(prefix='shieldvi-T015-real-') as temporary:
        for name,cwd in [('rollback-source',HERE/'rollback-source'),('canonical',AI)]:
            port=free_port();base=f'http://127.0.0.1:{port}'
            env=os.environ.copy()
            env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',CUDA_VISIBLE_DEVICES='',
                PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',AI_SERVICE_TOKEN=token,STORE_SUMMARIES='1',
                REVIEW_DB_PATH=str(Path(temporary)/f'{name}-reviews.sqlite3'),DB_PATH=str(Path(temporary)/f'{name}-summary.sqlite3'))
            env.pop('PYTHONPATH',None)
            if name=='rollback-source':env['MODEL_PATH']=str(ROOT/'models/visobert_head_refined')
            else:env.pop('MODEL_PATH',None)  # Verify approved default selection after relocation.
            command="import torch;torch.set_num_threads(2);import uvicorn;uvicorn.run('app.main:app',host='127.0.0.1',port="+str(port)+",proxy_headers=False)"
            with (HERE/f'{name}-real-server.txt').open('w',encoding='utf-8') as log:
                process=subprocess.Popen([sys.executable,'-c',command],cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=flags)
                try:
                    for _ in range(180):
                        if process.poll() is not None:raise RuntimeError(f'{name} real-model server exited')
                        try:
                            with urllib.request.urlopen(base+'/health',timeout=1) as response:
                                health=json.load(response)
                                if health['model_loaded']:break
                                raise RuntimeError(f'{name} did not load the real checkpoint')
                        except OSError:time.sleep(.25)
                    else:raise RuntimeError('Real-model server startup timed out')
                    def call(path,body=None,auth=False):
                        headers={'Content-Type':'application/json'}
                        if auth:headers['Authorization']='Bearer '+token
                        request=urllib.request.Request(base+path,headers=headers,method='POST' if body is not None else 'GET',
                            data=json.dumps(body).encode() if body is not None else None)
                        with urllib.request.urlopen(request,timeout=30) as response:
                            raw=response.read();return response.status,raw,response.headers
                    payload={'thread_id':'migration-synthetic','profile':'conservative','comments':[
                        {'comment_id':'c1','user_id':'actor1','text':'Xin chào, cảm ơn bạn.','timestamp':'2026-10-30T00:00:00Z'},
                        {'comment_id':'c2','user_id':'actor2','text':'Đm điện thoại hết pin.','timestamp':'2026-10-30T00:01:00Z','parent_id':'c1'},
                        {'comment_id':'c3','user_id':'actor2','text':'Mày đúng là đồ ngu.','timestamp':'2026-10-30T00:02:00Z','parent_id':'c1'}]}
                    analyze=json.loads(call('/api/analyze',payload)[1])
                    assert analyze['model_threshold']==.41
                    schema=json.loads(call('/openapi.json')[1])
                    static={}
                    html=call('/dashboard/')[1];static['/dashboard/']=hashlib.sha256(html).hexdigest()
                    for path in re.findall(r'(?:src|href)="(/dashboard/assets/[^\"]+)"',html.decode()):
                        static[path]=hashlib.sha256(call(path)[1]).hexdigest()
                    assert len(static)>=3
                    item=analyze['comments'][0]
                    call('/api/reviews/batch',{'thread_id':'migration-synthetic','reviewer_id':'fixture','items':[
                        {'comment_id':'c1','human_label':'uncertain','ai_label':'toxic' if item['toxic_for_moderation'] else 'clean',
                         'toxicity_score':item['toxicity_score'],'lexical_flag':False}]})
                    reviews=json.loads(call('/api/reviews?thread_id=migration-synthetic')[1])
                    assert len(reviews['items'])==1
                    assert call('/api/reviews/stats')[0]==200 and call('/api/reviews/export')[0]==200
                    assert len(json.loads(call('/api/recent')[1])['items'])==1
                    for path in ('/','/docs','/redoc'):assert call(path)[0]==200
                    internal=json.loads(call('/api/v1/moderate/comment',{'schema_version':'1.0','request_id':'migration-request',
                        'content_id':'migration-comment','content_revision':1,'content_type':'comment','user_id':'actor1',
                        'text':'Xin chào, cảm ơn bạn.','timestamp':'2026-10-30T00:00:00Z',
                        'context':{'post_id':'migration-post','source':'social-api','complete':False,'recent_comments':[]}},True)[1])
                    assert internal['model_threshold']==.41
                    runs[name]={'analyze':analyze,'internal':{k:v for k,v in internal.items() if k!='analyzed_at'},
                        'schema':schema,'static':static,'real_model_loaded':health['model_loaded']}
                    print(name+': real model, legacy routes, review roundtrip, static and internal contract PASS',flush=True)
                finally:stop(process,flags)
    before,after=runs['rollback-source'],runs['canonical']
    assert before['schema']==after['schema'],'OpenAPI contract changed'
    assert before['static']==after['static'],'Legacy static changed'
    assert before['analyze']==after['analyze'],'Real model legacy response changed'
    assert before['internal']==after['internal'],'Real model adapter response changed'
    record={'status':'PASS','real_cpu_inference':True,'synthetic_comments':3,'model_name':after['analyze']['model_name'],
        'threshold':.41,'legacy_response_equal':True,'internal_response_equal_except_timestamp':True,
        'openapi_equal':True,'static_byte_equal':True,'static_hashes':after['static'],
        'scores':[row['toxicity_score'] for row in after['analyze']['comments']],
        'review_roundtrip_both_layouts':True,'summary_roundtrip_both_layouts':True,
        'database_writes':'temporary_only','canonical_used_default_approved_checkpoint':True,
        'rollback_source_rehearsed_over_http':True,'owned_servers_stopped':True}
    (HERE/'real-http-smoke.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record,ensure_ascii=True),flush=True)


if __name__=='__main__':main()
