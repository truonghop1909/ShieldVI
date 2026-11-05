"""Measured CPU inference smoke on approved default checkpoint, no training."""
import json,os,sys,time,platform
from pathlib import Path
from datetime import datetime,timedelta,timezone
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'services/moderation-ai'));sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha

if __name__=='__main__':
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='-1',STORE_SUMMARIES='0')
    os.environ.pop('MODEL_PATH',None) # This isolated benchmark explicitly measures approved auto-selection.
    import torch
    torch.set_num_threads(2)
    from app.predictor import ViSoBERTPredictor,default_model_path
    from app.live_analysis import IncrementalAnalyzer,model_fingerprint
    from app.moderation_contract import ModerationRequest
    from app.signal_engine import analyze_thread_v2
    from app.schemas import AnalyzeRequest
    model=Path(default_model_path());before=file_sha(model/'model.safetensors')
    actual=ViSoBERTPredictor(str(model));assert actual.threshold==.41
    actual.predict_scores(['Bình luận khởi động CPU, không dùng làm benchmark.'])
    class Counting:
        threshold=.41;name=actual.name
        def __init__(self):self.texts=0
        def predict_scores(self,texts):self.texts+=len(texts);return actual.predict_scores(texts)
    base=datetime(2026,11,4,tzinfo=timezone.utc)
    rows=[{'comment_id':'a','user_id':'Alice','text':'Mình gửi lịch làm việc mới cho mọi người.','timestamp':base,'parent_id':None},
        {'comment_id':'b','user_id':'Bob','text':'Bạn đúng là đồ ngu.','timestamp':base+timedelta(minutes=1),'parent_id':'a'},
        {'comment_id':'c','user_id':'Bob','text':'Mày đúng là đồ vô dụng.','timestamp':base+timedelta(minutes=2),'parent_id':'a'}]
    full=Counting();full_outputs=[];started=time.perf_counter()
    for end in (1,2,3):full_outputs.append(analyze_thread_v2(AnalyzeRequest(thread_id='synthetic_benchmark',comments=rows[:end]),full))
    full_ms=(time.perf_counter()-started)*1000
    cached=Counting();engine=IncrementalAnalyzer(cached,model_fingerprint(actual));outputs=[];started=time.perf_counter()
    for i,row in enumerate(rows):
        payload=ModerationRequest(schema_version='1.0',request_id='req_'+row['comment_id'],content_id=row['comment_id'],content_revision=1,
            user_id=row['user_id'],text=row['text'],timestamp=row['timestamp'],parent_id=row['parent_id'],
            context={'post_id':'synthetic_benchmark','source':'social-api','complete':True,'recent_comments':rows[:i]})
        outputs.append(engine.analyze(payload))
    incremental_ms=(time.perf_counter()-started)*1000
    assert full.texts==6 and cached.texts==3 and outputs[-1].evidence[0].evidence_comment_ids==['b','c']
    for i,result in enumerate(outputs):assert result.toxicity_score==full_outputs[i]['comments'][i]['toxicity_score']
    assert file_sha(model/'model.safetensors')==before
    atomic_json(P/'T036_actual_benchmark.json',{'status':'PASS','hardware':platform.machine(),'cpu_threads':2,'device':'cpu',
        'model_path':str(model),'weights_sha256':before,'threshold':.41,'synthetic_comments':3,'warmup_excluded':True,
        'full_neural_texts':6,'incremental_neural_texts':3,'full_analysis_ms':full_ms,'incremental_analysis_ms':incremental_ms,
        'raw_current_score_invariant':True,'grounded_repeated_evidence':['b','c'],'training_performed':False,
        'default_changed':False,'independent_real_world_evaluation':False,'note':'Single small CPU smoke; timings are measured, not an SLO or statistically stable speedup.'})
    atomic_json(P/'T036_actual_outputs.json',[out.model_dump(mode='json') for out in outputs])
    print(json.dumps({'status':'PASS','full_neural_texts':6,'incremental_neural_texts':3,'full_ms':full_ms,'incremental_ms':incremental_ms}))
