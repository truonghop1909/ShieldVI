"""Read-only revalidation of retained actual training/evaluation receipts."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
OLD=ROOT/'reports/task_rollout_20261104'
def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def main():
    training=read(OLD/'T041_run_manifest.json');retained=read(OLD/'T041_retained.json');studio=Path(retained['studio_root'])
    candidate=studio/'training_runs'/training['run_id']/'candidate'
    for name,expected in training['files'].items():assert sha(candidate/name)==expected,name
    for value in training['dataset_sources'].values():assert sha(Path(value['path']))==value['sha256']
    assert training['synthetic_only'] and not training['human_gold'] and not training['activated'] and training['threshold']==.41
    concurrency=read(OLD/'T041_concurrency.json');browser=read(OLD/'T041_browser_result.json')
    assert browser['actual_training'] and browser['neural_reload'] and browser['status']=='PASS'
    save('T041_receipt_reverified.json',{'status':'PASS','actual_training_rerun':False,'historical_actual_training_verified':True,'candidate_sha256':training['candidate_sha256'],'run_id':training['run_id'],'files_verified':len(training['files']),'concurrency':concurrency,'source_receipt_sha256':sha(OLD/'T041_run_manifest.json')})
    report=read(OLD/'T042_evaluation.json');pointer=read(studio/'registry/latest.json');registry=studio/'registry'/pointer['file']
    assert sha(registry)==pointer['sha256']==report['registry_sha256']
    manifest=read(registry)
    for model_id in report['models']:
        model=manifest['models'][model_id];path=Path(model['path']);path=path if path.is_absolute() else ROOT/path
        assert sha(path/'model.safetensors')==model['sha256']['model.safetensors'],model_id
    for model in report['models'].values():
        for layer in ('raw','final'):
            m=model[layer];assert m['tp']+m['fp']+m['tn']+m['fn']==m['n']==4
            positive=2*m['tp']/(2*m['tp']+m['fp']+m['fn'])
            negative=2*m['tn']/(2*m['tn']+m['fp']+m['fn'])
            assert abs((positive+negative)/2-m['macro_f1'])<1e-12
        assert model['target']['recall'] is None and model['repeated']['recall'] is None
    assert report['threshold']==.41 and report['default_unchanged'] and not report['human_gold']
    save('T042_report_reverified.json',{'status':'PASS','actual_inference_rerun':False,'historical_actual_paired_inference_verified':True,'models':list(report['models']),'comments':report['comments'],'cohort_sha256':report['dataset_sha256'],'source_report_sha256':sha(OLD/'T042_evaluation.json'),'registry_sha256':report['registry_sha256'],'human_gold':False,'independent_real':False,'confusion_and_macro_f1_recomputed':True,'target_repeated_denominators':'absent, remain null'})
    print('PASS: retained actual CPU training/checkpoint/source hashes and paired evaluation receipts verified; no new training/inference.')
if __name__=='__main__':main()
