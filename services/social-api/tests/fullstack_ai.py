"""Explicitly gated synthetic AI with file-based fault injection; test use only."""
import json
import os
from pathlib import Path
import tempfile
import time

if os.environ.get('SHIELDVI_FULLSTACK_E2E')!='1':
    raise RuntimeError('Fullstack synthetic fixture requires explicit test mode')
CONTROL=Path(os.environ['SHIELDVI_AI_FAULT_FILE']).resolve()
if Path(tempfile.gettempdir()).resolve() not in CONTROL.parents:
    raise RuntimeError('Fault control must stay in disposable temporary directory')

from app.main import app,get_predictor
from fastapi import HTTPException


class SyntheticPredictor:
    name='FULLSTACK SYNTHETIC SCORES - NOT REAL INFERENCE'
    threshold=.41
    def predict_scores(self,texts):
        settings=json.loads(CONTROL.read_text(encoding='utf-8'))
        mode=settings['mode']
        if mode=='unavailable':raise HTTPException(503,'Injected synthetic AI outage')
        if mode not in {'normal','delayed'}:raise HTTPException(503,'Invalid synthetic fault mode')
        if mode=='delayed':time.sleep(1.5)
        return [.9 if '[TEST_TOXIC]' in text else .02 for text in texts]


app.dependency_overrides[get_predictor]=lambda:SyntheticPredictor()
