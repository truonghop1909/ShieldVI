"""E2E-only fake raw scores + actual default-v5 rules. Never a neural claim."""
import os,sys
from pathlib import Path
if os.environ.get('SHIELDVI_LIVE_E2E')!='1':raise RuntimeError('Test fixture is disabled')
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'services/moderation-ai'))
from fastapi import FastAPI,Depends,HTTPException
from pydantic import BaseModel,ConfigDict
from app.live_analysis import IncrementalAnalyzer
from app.moderation_contract import ModerationRequest
from app.moderation_adapter import service_auth

class FixturePredictor:
    threshold=.41;name='LIVE_E2E_SYNTHETIC_RAW_FIXTURE_NOT_NEURAL'
    def predict_scores(self,texts):return [.9 if 'ngu' in t.casefold() or 'vô dụng' in t.casefold() else .02 for t in texts]
class State(BaseModel):
    model_config=ConfigDict(extra='forbid')
    offline:bool
app=FastAPI();engine=IncrementalAnalyzer(FixturePredictor(),'f'*64);offline=False
@app.get('/health')
def health():return {'status':'ready','fixture':True,'neural_inference':False}
@app.post('/__test/state',dependencies=[Depends(service_auth)])
def state(payload:State):
    global offline
    offline=payload.offline;return {'offline':offline}
@app.post('/api/live/moderate/comment',dependencies=[Depends(service_auth)])
def moderate(payload:ModerationRequest):
    if offline:raise HTTPException(503,'Injected fixture outage')
    return engine.analyze(payload)
