"""One scoring pass after rule/input freeze, no post-score tuning."""
import json,os,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;D=R/'datasets/fixtures/v62_postfreeze_challenge_v1'
sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(R/'services/moderation-ai'));sys.path.insert(0,str(P))
from synthetic_data.pipeline import atomic_json,file_sha
from evaluate_research_v62 import annotated,write_cohort
from evaluate_synthetic_signals import classification
from progress import record

if __name__=='__main__':
    lock=P/'V62_LOCK.json';frozen=json.loads(lock.read_text());output=P/'postfreeze_challenge'
    assert not output.exists(),'Do not rescore/tune an already-seen challenge'
    for name,digest in frozen['files'].items():assert file_sha(R/name)==digest
    manifest=json.loads((D/'manifest.json').read_text());assert manifest['processor_lock_sha256']==file_sha(lock)
    threads=[json.loads((D/'threads'/(tid+'.json')).read_text()) for tid in manifest['thread_sha256']]
    for t in threads:assert file_sha(D/'threads'/(t['thread_id']+'.json'))==manifest['thread_sha256'][t['thread_id']]
    cache=P/'postfreeze_scores.json';model=R/'models/candidates/T029_synthetic_only_head_cpu_20261103_r06'
    assert file_sha(model/'model.safetensors')==frozen['r06_weights_sha256']
    if not cache.exists():
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0',CUDA_VISIBLE_DEVICES='-1')
        import torch
        torch.set_num_threads(4)
        from app.predictor import ViSoBERTPredictor
        predictor=ViSoBERTPredictor(str(model));assert predictor.threshold==.41
        values=predictor.predict_scores([c['text'] for t in threads for c in t['comments']])
        atomic_json(cache,{'scores':values,'actual_r06_inference':True,'model_sha256':frozen['r06_weights_sha256'],
            'manifest_sha256':file_sha(D/'manifest.json'),'training_performed':False})
    result=write_cohort(output,'paired',*annotated(D,cache))
    rows=json.loads((output/'paired/rows.json').read_text());result['raw']=classification([(r['reference'],'TOXIC' if r['raw_score']>=.41 else 'CLEAN') for r in rows])
    result.update(processor_lock_sha256=file_sha(lock),no_post_score_tuning=True,scope='same-author synthetic control/coverage challenge only, not human gold')
    atomic_json(output/'first_pass_metrics.json',result)
    for name,digest in frozen['files'].items():assert file_sha(R/name)==digest
    record('POSTFREEZE_CHALLENGE_SCORED_ONCE','New6threads/36comments authored after V62_LOCK, source references and manifests frozen before actualr06 CPUoffline scoring. First-pass classification/target/repeated/FPFN/evidence results retained; no post-score rule or label changes. Same-author synthetic only, not human gold/independent real. See postfreeze_challenge/first_pass_metrics.json; review all failures before conclusions.')
    print(json.dumps({k:result[k] for k in ('classification','grounding','new_label_errors','remaining_errors')}))
