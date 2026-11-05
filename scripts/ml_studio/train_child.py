"""Only a claimed T041 run can execute this bounded existing head trainer."""
import argparse,json,platform,sys
from pathlib import Path
from real_dataset.core import atomic_json,sha_file
from .datasets import DatasetStore,canonical,digest
from .training import TrainingJobs

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--run-id',required=True);args=parser.parse_args()
    store=DatasetStore(args.root);jobs=TrainingJobs(store);run=jobs.get(args.run_id)
    if run['status']!='RUNNING':raise ValueError('Training run is not claimed')
    path=store.root/'training_runs'/args.run_id;config=run['config'];flight=jobs.preflight(config)
    if json.loads((path/'config.json').read_text(encoding='utf-8'))!=config or flight!=run['preflight']:raise ValueError('Immutable configuration/preflight changed')
    prepared=path/'prepared';prepared.mkdir(exist_ok=False);rows=[r for identity in config['dataset_versions'] for r in store.rows(identity)]
    for split in ('train','validation'):
        selected=[r for r in rows if r['split']==split];counts={l:sum(r['label']==l for r in selected) for l in ('CLEAN','TOXIC')}
        output=[{'thread_id':r['thread_id'],'text':r['text'],'label':int(r['label']=='TOXIC'),'label_origin':'AI_synthetic_user_accepted','sample_weight':len(selected)/(2*counts[r['label']]) if config['balanced_class_weights'] else 1.} for r in selected]
        (prepared/(split+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in output),encoding='utf-8')
    atomic_json(prepared/'manifest.json',{'sources':flight['sources'],'threshold':.41,'human_gold':False,'test_not_used_for_training':True})
    from t029_cpu_head import train
    import torch
    torch.set_num_interop_threads(min(2,config['cpu_threads']))
    training={**config,'run_id':'T041_'+args.run_id,'output_dir':str(path/'candidate'),'max_training_seconds':config['max_seconds'],'feature_batch_size':8,'weight_decay':.01,'distillation_weight':.1}
    report=train(training,prepared,Path(flight['base_path']),flight)
    (path/'candidate/README.md').write_text('# T041 synthetic-only CPU head smoke\n\nFrozen encoder, new synthetic reference data only. Locked thread train/validation partition; test excluded from training/selection. Not r07, human gold, independent evaluation or model promotion. Threshold0.41; original/default checkpoints unchanged.\n',encoding='utf-8')
    import torch,transformers
    manifest={'schema_version':'studio-training-1.0','run_id':args.run_id,'status':'VERIFIED_HEAD_TRAINED_NOT_ACTIVATED','candidate_sha256':report['candidate_sha256'],'base_sha256':flight['base_sha256'],'config_sha256':sha_file(path/'config.json'),'dataset_sources':flight['sources'],'synthetic_only':True,'human_gold':False,'threshold':.41,'activated':False,'test_used_for_selection':False,
        'environment':{'python':platform.python_version(),'torch':torch.__version__,'transformers':transformers.__version__,'platform':platform.platform()},'files':{p.name:sha_file(p) for p in (path/'candidate').iterdir() if p.is_file()}}
    atomic_json(path/'run_manifest.json',manifest)
if __name__=='__main__':main()
