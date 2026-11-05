"""Process-local research demo using the canonical app and frozen v6.1 processor.

No default source/config, weights, readiness manifest or existing database edits.
"""
import hashlib,json,os,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'services/moderation-ai'))

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    lock=json.loads((R/'reports/ai_update/fresh10_recovery_20261103/experiment_lock_v2.json').read_text())
    assert digest(R/'services/moderation-ai/app/experiments/fresh10_v6.py')==lock['experimental_module_sha256']
    model=R/'models/candidates/T029_synthetic_only_head_cpu_20261103_r06'
    assert digest(model/'model.safetensors')=='e5090150ab0d951887060a4cefd25c223fe7d11aa23dd174fedf8b4f18abe3b2'
    os.environ.update(MODEL_PATH=str(model),STORE_SUMMARIES='0',DB_PATH=str(D/'summaries.sqlite3'),
        REVIEW_DB_PATH=str(D/'demo_reviews.sqlite3'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='-1')
    import torch
    torch.set_num_threads(4)
    import app.main as main
    from app.experiments.fresh10_v6 import analyze_thread_v6,CONTEXT_VERSION,TARGET_VERSION,REPEATED_VERSION
    from fastapi.responses import HTMLResponse,FileResponse,JSONResponse
    # Existing /api/v2/analyze resolves this global in this demo process only.
    main.analyze_thread_v2=analyze_thread_v6
    main.app.title='ShieldVI r06 + v6.1 — local research demo'
    index=R/'services/moderation-ai/app/static/index.html';assert index.is_file()
    banner='''<div style="position:relative;z-index:100;padding:12px 22px;background:#fff2c7;color:#493400;font:14px system-ui">
    <b>DEMO NGHIÊN CỨU — ViSoBERT r06 + Context/Target/Repeated v6.1</b> · Ngưỡng 0.41 · Nhãn tham khảo synthetic<br>
    <a href="/demo/threads/9">Tải input Test09</a> · <a href="/demo/threads/10">Tải input Test10</a> ·
    <a href="/demo/threads/7">Tải input Test07</a> · <a href="/api/demo/config" target="_blank">Thông tin phiên demo</a>
    </div>'''

    @main.app.middleware('http')
    async def research_marker(request,call_next):
        if request.url.path.startswith('/api/v1/'):
            return JSONResponse({'detail':'Local research demo; internal Social API is unavailable here'},status_code=404)
        if request.method=='GET' and request.url.path in ('/dashboard/','/dashboard/index.html'):
            response=HTMLResponse(index.read_text(encoding='utf-8').replace('<body>','<body>'+banner))
        else:response=await call_next(request)
        response.headers['X-ShieldVI-Demo']='r06-v6.1-research'
        return response

    @main.app.get('/api/demo/config')
    def config():
        predictor=getattr(main.app.state,'predictor',None)
        return {'mode':'local_research_only','model':'r06','model_loaded':predictor is not None,'threshold':.41,
                'rules':{'context':CONTEXT_VERSION,'target':TARGET_VERSION,'repeated':REPEATED_VERSION},
                'readiness_lock_modified':False,'default_modified':False,'training_performed':False,'human_gold':False}

    @main.app.get('/demo/threads/{number}')
    def thread(number:int):
        if number not in range(1,11):return JSONResponse({'detail':'Unknown example'},status_code=404)
        path=next((R/'datasets/fixtures/fresh10_regression_v1/inputs').glob('TEST'+str(number).zfill(2)+'_*.json'))
        return FileResponse(path,media_type='application/json',filename=path.name)

    import uvicorn
    uvicorn.run(main.app,host='127.0.0.1',port=8023,proxy_headers=False)

if __name__=='__main__':run()
