"""Independent-evaluation gate. Unverified/synthetic data cannot produce gold metrics."""
import argparse,hashlib,json,sys
from collections import Counter
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from evaluate_social_policy import binary_metrics
from prepare_ai_update_data import normalized,grams,NEAR_THRESHOLD

def development_exclusions():
    path=ROOT/'datasets/ai-update/review_v1/review.jsonl'
    rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
    return {r['thread_id'] for r in rows},{r['normalized_text'] for r in rows}

def evaluate(records,predictions):
    if not records:raise ValueError('No independent real human-verified evaluation records supplied')
    keys=[];labels=[];preds=[];uncertain=0
    seen_threads,seen_texts=development_exclusions()
    seen_grams=[grams(t) for t in seen_texts]
    for r in records:
        key=(r['thread_id'],r['comment_id'])
        if key in keys:raise ValueError('Duplicate evaluation ID')
        keys.append(key)
        if r.get('source_type') not in ('real_anonymized','real_licensed') or r.get('rights_status')!='approved' or not r.get('rights_reference'):
            raise ValueError('Independent real data with documented rights required')
        if r.get('split')!='blind_evaluation' or r.get('used_for_training') is not False or r.get('used_for_rule_development') is not False:
            raise ValueError('Blind evaluation isolation not established')
        if r.get('review_status')!='VERIFIED_SOLO' or not r.get('annotator_id') or not r.get('reviewed_at'):
            raise ValueError('Human verification missing')
        try:stamp=datetime.fromisoformat(r['reviewed_at'].replace('Z','+00:00'))
        except (ValueError,TypeError):raise ValueError('Invalid reviewer timestamp') from None
        if stamp.utcoffset() is None:raise ValueError('Reviewer timestamp requires timezone')
        raw=r.get('raw_text')
        if not isinstance(raw,str) or not raw.strip():raise ValueError('Raw evaluation text required for leakage check')
        key_text=normalized(raw);g=grams(key_text)
        if r['thread_id'] in seen_threads or key_text in seen_texts:raise ValueError('Evaluation overlaps development/training corpus')
        if any(len(g & other)/len(g | other)>=NEAR_THRESHOLD for other in seen_grams):raise ValueError('Near-duplicate evaluation leakage')
        if r.get('comment_label')=='UNCERTAIN':uncertain+=1;continue
        if r.get('comment_label') not in ('CLEAN','TOXIC'):raise ValueError('Unknown human label')
        if key not in predictions:raise ValueError('Missing prediction for verified example')
        if type(predictions[key]) is not int or predictions[key] not in (0,1):raise ValueError('Prediction must be binary integer')
        labels.append(int(r['comment_label']=='TOXIC'));preds.append(predictions[key])
    if set(predictions)!=set(keys):raise ValueError('Predictions must match the exact evaluation cohort')
    if not labels:raise ValueError('No determinate human labels; metrics unavailable')
    return {'metrics':binary_metrics(labels,preds),'excluded_uncertain':uncertain,'review_protocol':'single reviewer; no inter-annotator agreement claim','data_kind':'independent_real_verified'}

def gate(manifest):
    data=manifest.get('data_files',[])
    if not data:return {'status':'BLOCKED','reason':'No approved independent real dataset or human-verified labels; synthetic development fixtures cannot substitute','metrics':None}
    return {'status':'READY_FOR_VALIDATION','reason':'Run evaluate() on verified records and an exact prediction cohort; metadata alone is not a passing benchmark','metrics':None}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=gate(json.loads(args.manifest.read_text(encoding='utf-8')))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True));raise SystemExit(2 if result['status']=='BLOCKED' else 0)
