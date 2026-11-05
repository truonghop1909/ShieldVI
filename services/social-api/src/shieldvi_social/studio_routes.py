"""Admin-only opt-in Studio; clients never choose server filesystem paths."""
import sys,json
from pathlib import Path
from fastapi import APIRouter,Depends,Request,HTTPException,Query,Header
from uuid import UUID
from fastapi.responses import Response
from .dependencies import require_roles
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts'))
from ml_studio.datasets import DatasetStore,ImportInput,safe_csv
from ml_studio.annotations import StudioReviews,StudioAnnotation,RevisionConflict
from ml_studio.training import TrainingJobs,TrainingInput
from ml_studio.evaluation import EvaluationJobs,EvaluationInput
router=APIRouter(prefix='/api/studio',tags=['local-ml-studio']);admin=require_roles('admin')
def store(request):
    value=getattr(request.app.state,'studio',None)
    if value is None:raise HTTPException(503,'Studio requires an explicitly initialized root')
    return value
def lookup(request,identity):
    try:return store(request).get(identity)
    except KeyError:raise HTTPException(404,'Dataset not found')
@router.get('/datasets')
def datasets(request:Request,who=Depends(admin)):return {'items':store(request).list(),'roles':['admin'],'schema_version':'studio-1.0'}
@router.post('/datasets',status_code=201)
def upload(payload:ImportInput,request:Request,who=Depends(admin)):
    try:return store(request).import_dataset(payload,who.user.id)
    except KeyError:raise HTTPException(422,'Unknown parent version')
    except ValueError as error:raise HTTPException(422,str(error)[:180])
@router.get('/datasets/{identity}')
def detail(identity:str,request:Request,page:int=Query(1,ge=1,le=10000),who=Depends(admin)):
    value=lookup(request,identity);rows=store(request).rows(identity);value.update(items=rows[(page-1)*50:page*50],page=page,page_size=50,total=len(rows));return value
@router.get('/datasets/{identity}/export')
def export(identity:str,request:Request,format:str=Query('jsonl',pattern='^(csv|jsonl|report)$'),who=Depends(admin)):
    value=lookup(request,identity)
    if format=='report':return value
    rows=store(request).rows(identity);content=safe_csv(rows) if format=='csv' else ''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)
    return Response(content,media_type='text/csv' if format=='csv' else 'application/x-ndjson',headers={'Content-Disposition':f'attachment; filename="dataset-{identity}.{format}"','Cache-Control':'no-store'})

def reviews(request,identity):
    lookup(request,identity)
    try:return StudioReviews(store(request),identity)
    except ValueError as error:raise HTTPException(409,str(error))

@router.get('/annotations/{identity}')
def annotations(identity:str,request:Request,page:int=Query(1,ge=1,le=10000),who=Depends(admin)):
    value=reviews(request,identity);threads=list(value.corpus().values());rows=value.visible(who.user.id)
    return {'dataset_version':identity,'threads':threads[page-1:page],'page':page,'total_threads':len(threads),'total_comments':sum(len(t['comments']) for t in threads),'reviews':rows,'reviewer_id':who.user.id,'blind_mode':True,
            'human_gold':False,'round2_gap_seconds':300 if value.origin=='real' else 0,'source_kind':value.origin,'completed_round2':sum(r['review_round']==2 and r['round2_valid'] and r['annotation_status']=='ROUND2_DONE' for r in rows)}

@router.post('/annotations/{identity}')
def save_annotation(identity:str,payload:dict,request:Request,who=Depends(admin)):
    if payload.get('reviewer_id',who.user.id)!=who.user.id:raise HTTPException(403,'Reviewer must be the authenticated user')
    value=reviews(request,identity)
    try:return value.save(StudioAnnotation.model_validate({**payload,'reviewer_id':who.user.id}).model_dump())
    except RevisionConflict as error:raise HTTPException(409,str(error))
    except ValueError as error:raise HTTPException(422,str(error).split('\n')[0][:180])

@router.get('/annotations/{identity}/history')
def annotation_history(identity:str,thread_id:str,comment_id:str,request:Request,who=Depends(admin)):
    return {'items':reviews(request,identity).history(thread_id,comment_id),'human_gold':False}

@router.post('/annotations/{identity}/snapshot')
def annotation_snapshot(identity:str,request:Request,who=Depends(admin)):
    try:return reviews(request,identity).snapshot(who.user.id)
    except ValueError as error:raise HTTPException(409,str(error))

@router.get('/training-runs')
def training_runs(request:Request,who=Depends(admin)):return {'items':TrainingJobs(store(request)).list()}
@router.post('/training-runs/preflight')
def preflight_training(payload:TrainingInput,request:Request,who=Depends(admin)):
    try:return TrainingJobs(store(request)).preflight(payload)
    except (ValueError,KeyError,FileNotFoundError) as error:raise HTTPException(422,str(error)[:180])
@router.post('/training-runs',status_code=201)
def create_training(payload:TrainingInput,request:Request,idempotency_key:UUID=Header(alias='Idempotency-Key'),who=Depends(admin)):
    try:return TrainingJobs(store(request)).create(payload,who.user.id,idempotency_key)
    except (ValueError,KeyError,FileNotFoundError) as error:raise HTTPException(422,str(error)[:180])
@router.get('/training-runs/{identity}')
def training_run(identity:str,request:Request,who=Depends(admin)):
    try:return TrainingJobs(store(request)).get(identity)
    except KeyError:raise HTTPException(404,'Training run not found')
@router.post('/training-runs/{identity}/cancel')
def cancel_training(identity:str,request:Request,who=Depends(admin)):
    try:return TrainingJobs(store(request)).cancel(identity,who.user.id)
    except KeyError:raise HTTPException(404,'Training run not found')

@router.get('/training-runs/{identity}/logs')
def training_logs(identity:str,request:Request,who=Depends(admin)):
    jobs=TrainingJobs(store(request))
    try:jobs.get(identity)
    except KeyError:raise HTTPException(404,'Training run not found')
    path=store(request).root/'training_runs'/identity/'worker.log'
    if not path.exists():return {'text':''}
    with path.open('rb') as stream:
        stream.seek(max(0,path.stat().st_size-32768));data=stream.read(32768)
    return {'text':data.decode('utf-8',errors='replace'),'truncated':path.stat().st_size>32768}

@router.get('/models')
def models(request:Request,who=Depends(admin)):
    try:return EvaluationJobs(store(request)).list_models()
    except ValueError as error:raise HTTPException(503,str(error))
@router.post('/models/{identity}/promote')
def promote_model(identity:str,request:Request,who=Depends(admin)):
    raise HTTPException(409,'Promotion BLOCKED: independent human gold, formal quality gates and explicit production approval are missing; no default changed')
@router.get('/evaluations')
def evaluations(request:Request,who=Depends(admin)):return {'items':EvaluationJobs(store(request)).list()}
@router.post('/evaluations',status_code=201)
def create_evaluation(payload:EvaluationInput,request:Request,who=Depends(admin)):
    try:return EvaluationJobs(store(request)).create(payload,who.user.id)
    except (ValueError,KeyError) as error:raise HTTPException(422,str(error)[:180])
@router.get('/evaluations/{identity}')
def evaluation_detail(identity:str,request:Request,who=Depends(admin)):
    try:return EvaluationJobs(store(request)).get(identity)
    except KeyError:raise HTTPException(404,'Evaluation not found')
@router.get('/evaluations/{identity}/export')
def evaluation_export(identity:str,request:Request,format:str=Query('json',pattern='^(json|csv|md)$'),who=Depends(admin)):
    try:value=EvaluationJobs(store(request)).get(identity)
    except KeyError:raise HTTPException(404,'Evaluation not found')
    report=value['report']
    if not report:raise HTTPException(409,'Evaluation report not ready')
    if format=='json':content=json.dumps(report,ensure_ascii=False,indent=2);mime='application/json'
    elif format=='csv':content=safe_csv(report['errors']);mime='text/csv'
    else:
        content='# Synthetic development evaluation\n\nNot human gold or independent real-world evaluation. Threshold0.41; default unchanged.\n\n| Model | Raw Macro-F1 | Final Macro-F1 | TP/FP/FN/TN |\n|---|---:|---:|---|\n'
        for key,data in report['models'].items():
            m=data['final'];content+=f"| {key} | {data['raw']['macro_f1']:.4f} | {m['macro_f1']:.4f} | {m['tp']}/{m['fp']}/{m['fn']}/{m['tn']} |\n"
        content+='\nTarget/repeated/evidence without reference denominators are unavailable; see full JSON for coverage.\n';mime='text/markdown'
    return Response(content,media_type=mime,headers={'Content-Disposition':f'attachment; filename="evaluation-{identity}.{format}"','Cache-Control':'no-store'})
