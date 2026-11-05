"""Correct a reporting mask from the same saved predictions; no new inference/tuning."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from evaluate_synthetic_candidate import is_teencode
from evaluate_synthetic_signals import classification
from refine_model import metrics
from synthetic_data.pipeline import atomic_json,file_sha
path=P/'evaluation/predictions.json';rows=json.loads(path.read_text(encoding='utf-8'));result={}
for name in ('V1','r05','r06'):
    result[name]={}
    for split in ('synthetic_validation','synthetic_challenge'):
        selected=[r for r in rows if r['model']==name and r['split']==split and r['synthetic_reference']!='UNCERTAIN' and is_teencode(r['text'])]
        raw=metrics([int(r['synthetic_reference']=='TOXIC') for r in selected],[r['raw_score'] for r in selected],.41) if selected else {'n':0}
        hybrid=classification([(r['synthetic_reference'],r['advisory']) for r in selected])
        result[name][split]={'raw':raw,'hybrid':hybrid}
atomic_json(P/'evaluation/teencode_reporting_v2.json',{'source_predictions_sha256':file_sha(path),'metrics':result,
  'reason':'Original reporting regex omitted user-requested single-letter t/m/k and accented đm/vl forms. Corrected mask only; reference labels, model predictions and aggregate metrics unchanged.',
  'new_model_inference_performed':False,'hyperparameters_changed':False,'scope':'heuristic teencode slice, not a human annotation'})
print(json.dumps({'teencode_rows':{split:result['r06'][split]['raw']['n'] for split in ('synthetic_validation','synthetic_challenge')},'new_inference':False}))
