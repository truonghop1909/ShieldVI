"""Offline CPU-only evaluation. Never trains, selects thresholds, or emits raw text.

ViCTSD toxicity gold is separate from synthetic regression and unlabelled policy
severity/target/repeated tasks. Lexical/hybrid metrics measure review screening.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
THRESHOLD=.41


def sha(path):
    with Path(path).open('rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()


def fraction(n,d):
    return n/d if d else None


def wilson(n,d):
    if not d:return None
    z=1.959963984540054;p=n/d;den=1+z*z/d
    center=(p+z*z/(2*d))/den
    width=z*math.sqrt(p*(1-p)/d+z*z/(4*d*d))/den
    return [max(0,center-width),min(1,center+width)]


def binary_metrics(labels,predictions):
    if not labels or len(labels)!=len(predictions) or any(type(v) is not int or v not in (0,1) for v in [*labels,*predictions]):
        raise ValueError('Expected equal nonempty sequences of binary integer labels')
    counts=Counter(zip(labels,predictions))
    tn,fp,fn,tp=(counts[(0,0)],counts[(0,1)],counts[(1,0)],counts[(1,1)])
    positive_f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0
    negative_f1=2*tn/(2*tn+fp+fn) if 2*tn+fp+fn else 0
    return {'n':len(labels),'support':{'clean':tn+fp,'toxic':tp+fn},'confusion_matrix':[[tn,fp],[fn,tp]],
        'matrix_rows':'gold clean,toxic','matrix_columns':'predicted negative,positive',
        'precision':fraction(tp,tp+fp),'recall':fraction(tp,tp+fn),'f1':positive_f1,
        'macro_f1':(positive_f1+negative_f1)/2,'accuracy':(tp+tn)/len(labels),
        'false_positive_rate':fraction(fp,fp+tn),'false_negative_rate':fraction(fn,fn+tp),
        'fpr_wilson_95':wilson(fp,fp+tn),'fnr_wilson_95':wilson(fn,fn+tp)}


def latency(values):
    values=sorted(values)
    return {'n':len(values),'median_ms':statistics.median(values) if values else None,
        'p95_ms':values[max(0,math.ceil(.95*len(values))-1)] if values else None,
        'sum_ms':sum(values)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--limit',type=int,default=1000)
    parser.add_argument('--threads',type=int,default=2)
    args=parser.parse_args()
    if not 1<=args.limit<=1000 or not 1<=args.threads<=4:parser.error('limit 1..1000, CPU threads 1..4')
    output=args.output.resolve()
    if ROOT.parent not in output.parents:parser.error('Write evaluation artifacts within workspace')
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',CUDA_VISIBLE_DEVICES='')
    sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'services/social-api/src'))
    import torch
    torch.set_num_threads(args.threads)
    from app.predictor import ViSoBERTPredictor,default_model_path
    from app.moderation_adapter import moderate,LEXICON_VERSION
    from app.moderation_contract import ModerationRequest
    from shieldvi_social.policy import policy_outcome
    source=ROOT/'datasets/raw/victsd/ViCTSD_test.csv'
    manifest=json.loads((ROOT/'datasets/manifest.json').read_text(encoding='utf-8'))
    provenance=manifest['sources']['victsd']
    expected=next(row for row in provenance['raw_files'] if row['split']=='test')
    if sha(source)!=expected['sha256']:raise ValueError('Official test snapshot hash mismatch; refusing evaluation')
    with source.open(encoding='utf-8-sig',newline='') as handle:rows=list(csv.DictReader(handle))
    if len(rows)!=1000:raise ValueError('Expected unchanged official 1000-row holdout')
    rows=rows[:args.limit]
    texts=[row['Comment'] for row in rows];labels=[int(row['Toxicity']) for row in rows]
    synthetic_path=ROOT/'datasets/review/mxh_style_challenge.json'
    synthetic=json.loads(synthetic_path.read_text(encoding='utf-8'))
    if synthetic['is_gold'] is not False or synthetic['training_eligible'] is not False:
        raise ValueError('Synthetic provenance must be explicit')
    synthetic_texts=[row['text'] for row in synthetic['items']]
    checkpoint=Path(default_model_path()).resolve()
    started=datetime.now(timezone.utc).isoformat();start=time.perf_counter()
    predictor=ViSoBERTPredictor(str(checkpoint))
    load_seconds=time.perf_counter()-start
    if str(predictor.device)!='cpu' or predictor.threshold!=THRESHOLD:raise ValueError('CPU/0.41 invariant violated')
    predictor.predict_scores(['Xin chào.'])  # Warm-up excluded from sample latency.
    probabilities=[];batch_ms=[];amortized=[]
    all_texts=texts+synthetic_texts
    for start_index in range(0,len(all_texts),16):
        batch=all_texts[start_index:start_index+16];before=time.perf_counter()
        scores=predictor.predict_scores(batch);elapsed=(time.perf_counter()-before)*1000
        if len(scores)!=len(batch) or any(not math.isfinite(v) or not 0<=v<=1 for v in scores):raise ValueError('Invalid real model scores')
        probabilities.extend(scores);batch_ms.append(elapsed);amortized.extend([elapsed/len(batch)]*len(batch))
        print(f'CPU inference completed {min(start_index+16,len(all_texts))}/{len(all_texts)}',flush=True)
    lookup=dict(zip(all_texts,probabilities))
    class CachedRealScores:
        threshold=THRESHOLD
        name=predictor.name
        def predict_scores(self,items):return [lookup[text] for text in items]
    cached=CachedRealScores();timestamp=datetime.now(timezone.utc)
    def analyze(items,prefix):
        predictions=[];lexical=[];hybrid=[];risks=Counter();states=Counter();durations=[];unknown_targets=0
        for index,text in enumerate(items):
            payload=ModerationRequest(schema_version='1.0',request_id=f'{prefix}-request-{index}',content_id=f'{prefix}-{index}',
                content_revision=1,content_type='comment',user_id=f'{prefix}-actor-{index}',text=text,timestamp=timestamp,
                context={'post_id':f'{prefix}-post-{index}','source':'social-api','complete':False,'recent_comments':[]})
            before=time.perf_counter();result=moderate(payload,cached)
            risk,visibility,review=policy_outcome(result)
            durations.append((time.perf_counter()-before)*1000)
            predictions.append(int(result.ai_label=='TOXIC'))
            lexical.append(int(result.lexical_review_recommended))
            hybrid.append(int(review=='QUEUED'));risks[risk]+=1;states[visibility]+=1
            unknown_targets+=result.target_evidence.target_user_id is None
        return predictions,lexical,hybrid,{'risk_counts':dict(risks),'visibility_counts':dict(states),
            'review_load':fraction(sum(hybrid),len(items)),'review_count':sum(hybrid),
            'target_unknown_fraction':fraction(unknown_targets,len(items)),'adapter_cached_postprocess':latency(durations)}
    model,lexical,hybrid,policy=analyze(texts,'victsd')
    _,_,_,synthetic_policy=analyze(synthetic_texts,'synthetic')
    assert not set(policy['visibility_counts'])-{'PUBLISHED','PUBLISHED_FLAGGED'}
    record={'started_at_utc':started,'finished_at_utc':datetime.now(timezone.utc).isoformat(),
        'mode':'real_checkpoint_cpu_inference','model':{'name':predictor.name,'path_relative':str(checkpoint.relative_to(ROOT)),
            'weights_sha256':sha(checkpoint/'model.safetensors'),'threshold_config_sha256':sha(checkpoint/'threshold_config.json'),
            'threshold':THRESHOLD,'lexicon_sha256':LEXICON_VERSION,'device':str(predictor.device),'cpu_threads':args.threads,
            'load_seconds':load_seconds,'torch':torch.__version__,'transformers':importlib.metadata.version('transformers')},
        'dataset':{'name':'ViCTSD original official test local copy','path':str(source.relative_to(ROOT)),
            'sha256':expected['sha256'],'n':len(rows),'full_official_test':len(rows)==1000,
            'source':provenance['source'],'license':provenance['license'],'label_origin':provenance['label_origin'],
            'selection':'all original rows in original order; no resplit/filter/tuning','blind_holdout':False,
            'blind_note':'Official test has been inspected in earlier project reports; this is reproduction, not a fresh blind holdout.'},
        'classifier':binary_metrics(labels,model),
        'lexicon_screening_vs_toxicity_proxy':binary_metrics(labels,lexical),
        'hybrid_review_screening_vs_toxicity_proxy':binary_metrics(labels,hybrid),
        'policy_shadow':policy,'latency':{'real_forward_batches':latency(batch_ms),'amortized_per_item':latency(amortized),
            'note':'Warm-up excluded. 16-item CPU batches, including separately reported synthetic inputs. Not HTTP or singleton production latency.'},
        'synthetic_separate':{'dataset_id':synthetic['dataset_id'],'sha256':sha(synthetic_path),'n':len(synthetic_texts),
            'is_gold':False,'classification_quality':None,'policy_behavior_only':synthetic_policy},
        'not_evaluated':{'high_auto_hold_precision_recall_fp_fn':None,'target_precision_recall':None,'repeated_event_f1':None,
            'reason':'No independent human-labelled HIGH/target/thread-event gold. ViCTSD toxicity is not policy severity or harassment.'},
        'recommendation':{'high_auto_hold_enabled':False,'reason':'No calibrated HIGH rule, independent thread gold or activation approval.'},
        'privacy':{'raw_text_exported':False,'per_row_predictions_exported':False,'network_downloads':False,'training':False,
            'live_social_db_accessed':False,'threshold_changed':False},
        'source_hashes':{'evaluator':sha(__file__),'active_policy':sha(ROOT/'services/social-api/src/shieldvi_social/policy.py'),
            'predictor':sha(ROOT/'app/predictor.py'),'adapter':sha(ROOT/'app/moderation_adapter.py')}}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'complete','n':len(rows),'model':predictor.name,'macro_f1':record['classifier']['macro_f1'],
        'review_load':policy['review_load'],'high_auto_hold_enabled':False},ensure_ascii=True),flush=True)


if __name__=='__main__':main()
