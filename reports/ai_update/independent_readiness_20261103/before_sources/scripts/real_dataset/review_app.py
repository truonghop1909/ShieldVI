"""Loopback-only blind labeling UI. No model imports, predictions, or external assets."""
import argparse,json,secrets
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import FileResponse,JSONResponse,Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from .core import DATA,load_json
from .store import ReviewStore,AnnotationInput,RevisionConflict

def create_app(data_root=DATA,test_mode=False,store_factory=ReviewStore,profile=None):
    profile=profile or {'mode':'real'};synthetic=profile.get('mode')=='synthetic'
    root=Path(data_root);store=store_factory(root);review_model=store.annotation_model;token=secrets.token_urlsafe(36)
    app=FastAPI(title='ShieldVI — gán nhãn độc lập',docs_url=None,redoc_url=None,openapi_url=None)
    app.state.store=store
    @app.middleware('http')
    async def local_only(request:Request,call_next):
        host=urlsplit(str(request.base_url)).hostname
        allowed={'127.0.0.1','localhost'}|({'testserver'} if test_mode else set())
        if host not in allowed:return JSONResponse({'detail':'Loopback host required'},status_code=403)
        if request.method in ('POST','PUT','DELETE','PATCH'):
            if request.headers.get('x-review-token')!=token:return JSONResponse({'detail':'Review session token required'},status_code=403)
            origin=request.headers.get('origin')
            if origin and origin.rstrip('/')!=str(request.base_url).rstrip('/'):return JSONResponse({'detail':'Cross-origin write refused'},status_code=403)
            if int(request.headers.get('content-length','0') or 0)>30_000_000:return JSONResponse({'detail':'Request too large'},status_code=413)
        result=await call_next(request)
        result.headers['Cache-Control']='no-store'
        result.headers['X-Content-Type-Options']='nosniff'
        result.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"
        return result
    @app.exception_handler(RevisionConflict)
    async def conflict(request,exc):return JSONResponse({'detail':str(exc)},status_code=409)
    @app.exception_handler(ValueError)
    async def invalid(request,exc):return JSONResponse({'detail':str(exc)},status_code=422)
    @app.get('/session')
    def session():return {**profile,'token':token,'blind_review':not synthetic,'model_predictions_enabled':False,'locked':(root/'manifests/evaluation_lock.json').exists(),'test_mode':test_mode}
    @app.get('/api/threads')
    def threads(reviewer_id:str|None=None):
        if synthetic:return store.summaries(reviewer_id)
        data=store.corpus();rows=store.list_reviews();latest={}
        for r in rows:
            key=(r['thread_id'],r['comment_id'])
            if key not in latest or r['updated_at']>latest[key]['updated_at']:latest[key]=r
        labeled={(r['thread_id'],r['comment_id']) for r in rows if r['label']}
        return {'items':[{'thread_id':t['thread_id'],'topic':t['topic'],'source_platform':t['source_platform'],'source_url':t['source_url'],
                 'comments':len(t['comments']),'users':len({c['user_id'] for c in t['comments'] if c['user_id']}),'labeled':sum((t['thread_id'],c['comment_id']) in labeled for c in t['comments']),'label_counts':{label:sum(latest.get((t['thread_id'],c['comment_id']),{}).get('label')==label for c in t['comments']) for label in ('CLEAN','TOXIC','UNCERTAIN')}} for t in data.values()],
            'progress':load_json(root/'manifests/progress.json',{}),'counts':{'threads':len(data),'comments':sum(len(t['comments']) for t in data.values()),'labeled':len(labeled)}}
    @app.get('/api/threads/{thread_id}')
    def thread(thread_id:str):
        value=store.corpus().get(thread_id)
        if not value:raise HTTPException(404,'Thread not found')
        return value
    @app.get('/api/reviews')
    def reviews(thread_id:str,reviewer_id:str,review_round:int=1):return {'items':store.list_reviews(thread_id,reviewer_id,review_round),'round1':store.list_reviews(thread_id,reviewer_id,1)}
    @app.post('/api/reviews')
    def save(payload:review_model):return store.save(payload.model_dump())
    @app.get('/api/history/{thread_id}/{comment_id}')
    def history(thread_id:str,comment_id:str):return {'items':store.history(thread_id,comment_id)}
    class ThreadCheck(BaseModel):
        thread_id:str
        reviewer_id:str=Field(pattern=r'^[A-Za-z0-9_-]{1,40}$')
        source_reviewed:bool
        privacy_reviewed:bool
        completeness_reviewed:bool
    @app.get('/api/thread-checks/{thread_id}')
    def get_checks(thread_id:str,reviewer_id:str):
        with store.connect() as db:
            row=db.execute('SELECT * FROM thread_checks WHERE thread_id=? AND reviewer_id=?',(thread_id,reviewer_id)).fetchone()
        return dict(row) if row else {}
    @app.post('/api/thread-checks')
    def check(payload:ThreadCheck):
        if synthetic:raise HTTPException(409,'Synthetic không có bước xác minh nguồn thật T028.')
        store.check_thread(**payload.model_dump());return {'saved':True}
    @app.get('/api/export.csv')
    def export(reviewer_id:str|None=None):return Response(store.export_csv(reviewer_id),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="shieldvi_human_annotations.csv"'})
    @app.get('/api/reviewed.jsonl')
    def reviewed(reviewer_id:str):
        if not synthetic:raise HTTPException(404,'Synthetic export only')
        rows=store.reviewed_records(reviewer_id)
        return Response(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),media_type='application/x-ndjson',headers={'Content-Disposition':'attachment; filename=shieldvi_reviewed_synthetic.jsonl'})
    class CsvImport(BaseModel):text:str=Field(max_length=20_000_000)
    @app.post('/api/import.csv')
    def csv_import(payload:CsvImport):return {'imported':store.import_csv(payload.text)}
    class LockRequest(BaseModel):reviewer_id:str
    @app.post('/api/lock')
    def lock(payload:LockRequest):
        if synthetic:raise HTTPException(409,'Synthetic không phải tập đánh giá thật T028; chỉ xuất bản đã duyệt.')
        return store.lock_evaluation(payload.reviewer_id)
    ui=Path(__file__).parent/'review_ui'
    @app.get('/')
    def index():return FileResponse(ui/'index.html')
    app.mount('/assets',StaticFiles(directory=str(ui)),name='review-assets')
    return app

def main():
    import uvicorn
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8010);args=p.parse_args()
    if not 1024<=args.port<=65535:p.error('Choose a local port 1024..65535')
    print('ShieldVI blind human review: http://127.0.0.1:'+str(args.port))
    uvicorn.run(create_app(),host='127.0.0.1',port=args.port)
