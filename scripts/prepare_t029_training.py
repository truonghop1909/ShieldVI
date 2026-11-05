"""T029 data/config preparation only: immutable held-outs, no optimizer/model downloads."""
from __future__ import annotations
import argparse,csv,json,math
from collections import Counter,defaultdict
from pathlib import Path
from refine_model import normalize,file_hash,read_rows,clean_train
from synthetic_data.pipeline import atomic_json
ROOT=Path(__file__).resolve().parents[1]

def resolve(root,path):
    p=Path(path);return p if p.is_absolute() else Path(root)/p

def validate_config(config):
    if config['threshold']!=0.41:raise ValueError('Threshold must remain 0.41')
    if not 1<=config['epochs']<=10 or not 1<=config['batch_size']<=128 or not 1<=config['gradient_accumulation_steps']<=64:raise ValueError('Bounded epochs/batch required')
    synthetic_only=config.get('data_recipe')=='synthetic_only'
    ratio_ok=config['max_synthetic_fraction']==1 if synthetic_only else 0<config['max_synthetic_fraction']<=.5
    if not 0<config['learning_rate']<=.001 or not ratio_ok:raise ValueError('Invalid LR/augmentation ratio')
    if synthetic_only and (config.get('original_train') is not None or config.get('evaluation_protocol')!='synthetic_development' or config.get('synthetic_format')!='genz_v2'):
        raise ValueError('Synthetic-only experiment must exclude real training and retain synthetic provenance')
    if not .8<=config['near_duplicate_threshold']<=1 or not 20<=config['near_duplicate_min_chars']<=200:raise ValueError('Invalid similarity threshold')
    if not 16<=config['max_length']<=512 or not 1<=config['max_training_seconds']<=14400:raise ValueError('Bounded length/time required')
    if not 0<config['synthetic_loss_weight']<=2 or config['early_stopping_patience']<1:raise ValueError('Invalid weight/patience')
    if config.get('evaluation_protocol','real_independent') not in ('real_independent','synthetic_development'):raise ValueError('Unknown evaluation protocol')
    strategy=config.get('training_strategy','full_finetune_gpu')
    if strategy not in ('full_finetune_gpu','frozen_encoder_head_cpu'):raise ValueError('Unknown training strategy')
    if strategy=='frozen_encoder_head_cpu':
        if config['resource']!='local_CPU' or config.get('maximum_external_cost')!=0:raise ValueError('CPU alternative cannot use paid or external resources')
        if not 1<=config.get('cpu_threads',0)<=4 or not 1<=config.get('feature_batch_size',0)<=32:raise ValueError('CPU resource limits exceeded')
        if config['max_training_seconds']>900 or config['epochs']>3 or config['gradient_accumulation_steps']!=1 or config['learning_rate']>.0001:raise ValueError('CPU experiment exceeds bounded recipe')
        if config.get('evaluation_protocol')!='synthetic_development' or config.get('synthetic_format')!='genz_v2':raise ValueError('CPU alternative requires verified GenZ research protocol')
        if not 0<=config.get('distillation_weight',-1)<=1:raise ValueError('Invalid CPU distillation weight')
    return config

def chargrams(text):return {text[i:i+5] for i in range(max(1,len(text)-4))}

def remove_near(rows,heldout,threshold=.9,min_chars=40):
    signatures=[];postings=defaultdict(list)
    for text in set(normalize(s) for s in heldout if len(normalize(s))>=min_chars):
        g=chargrams(text);index=len(signatures);signatures.append(g)
        for token in g:postings[token].append(index)
    kept=[];removed=[]
    for row in rows:
        text=normalize(row['text']);found=False
        if len(text)>=min_chars:
            g=chargrams(text);hits=Counter(index for token in g for index in postings.get(token,()))
            for index,intersection in hits.items():
                if intersection/(len(g)+len(signatures[index])-intersection)>=threshold:found=True;break
        (removed if found else kept).append(row)
    return kept,removed

def prepare(config_path,output,base_model,root=ROOT):
    root=Path(root);output=Path(output);config_path=Path(config_path)
    cfg=validate_config(json.loads(config_path.read_text(encoding='utf-8')))
    if cfg.get('data_recipe')=='synthetic_only':
        from synthetic_data.experiment import prepare
        return prepare(config_path,output,base_model,root)
    base=Path(base_model).resolve()
    for name in ('config.json','model.safetensors','threshold_config.json','tokenizer_config.json'):
        if not (base/name).is_file():raise ValueError('Original checkpoint missing '+name)
    if json.loads((base/'threshold_config.json').read_text(encoding='utf-8'))['threshold']!=.41:raise ValueError('Base threshold mismatch')
    train_path=resolve(root,cfg['original_train']);val_path=resolve(root,cfg['validation']);test_path=resolve(root,cfg['test_text_only'])
    synth_dir=resolve(root,cfg['synthetic_export']);genz=cfg.get('synthetic_format')=='genz_v2'
    challenge=[]
    if genz:
        from synthetic_data.genz import verified_export
        synth_manifest,threads,_=verified_export(synth_dir)
        manifest_path=synth_dir/'dataset_manifest.json'
        challenge=[c['text'] for t in threads if t['split']=='development_challenge' for c in t['comments']]
        original_synth=[{'thread_id':t['thread_id'],'comment_id':c['comment_id'],'text':c['text'],
          'label':int(c['annotation']['label']=='TOXIC'),'comment_label':c['annotation']['label'],'label_source':'synthetic','human_gold':False}
          for t in threads if t['split']=='train' for c in t['comments']
          if c['annotation']['label']!='UNCERTAIN' and not c['annotation']['needs_human_review']]
        synth_manifest={**synth_manifest,'manual_review_performed':False,'excluded_uncertain':synth_manifest['labels']['UNCERTAIN']}
    else:
        manifest_path=synth_dir/'manifest.json';synth_manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        original_synth=[json.loads(line) for line in (synth_dir/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    for name,sha in synth_manifest['output_sha256'].items():
        if file_hash(synth_dir/name)!=sha:raise ValueError('Synthetic export checksum mismatch')
    if synth_manifest['manual_review_performed'] or synth_manifest['human_gold']:raise ValueError('This run must retain AI-only label provenance')
    # Test labels are never read for selection or scoring; only raw text is used to exclude leakage.
    validation=read_rows(val_path);test_text=read_rows(test_path,with_labels=False)
    heldout=[row['text'] for row in validation+test_text]+challenge
    gold,clean=clean_train(read_rows(train_path),heldout)
    gold,near_gold=remove_near(gold,heldout,cfg['near_duplicate_threshold'],cfg['near_duplicate_min_chars'])
    synth=[]
    for row in original_synth:
        if row.get('label_source')!='synthetic' or row.get('human_gold') is not False or row.get('comment_label') not in ('CLEAN','TOXIC') or row.get('label')!=int(row['comment_label']=='TOXIC'):raise ValueError('Invalid AI label/provenance')
        synth.append({'id':row['thread_id']+':'+row['comment_id'],'thread_id':row['thread_id'],'comment_id':row['comment_id'],'text':row['text'],'label':row['label']})
    synth,synth_clean=clean_train(synth,heldout)
    synth,near_synth=remove_near(synth,heldout,cfg['near_duplicate_threshold'],cfg['near_duplicate_min_chars'])
    # Cross-source exact/near copies are removed from synthetic, not relabeled as original gold.
    gold_keys={normalize(row['text']) for row in gold};overlaps=[row for row in synth if normalize(row['text']) in gold_keys]
    synth=[row for row in synth if normalize(row['text']) not in gold_keys]
    synth,near_cross=remove_near(synth,[row['text'] for row in gold],cfg['near_duplicate_threshold'],cfg['near_duplicate_min_chars'])
    ratio=len(synth)/(len(gold)+len(synth)) if gold or synth else 0
    if not gold or not synth or ratio>cfg['max_synthetic_fraction']:raise ValueError('Empty source or synthetic fraction exceeds proposed config; do not silently resample')
    rows=[{**row,'label_origin':'ViCTSD_original','sample_weight':1.0} for row in gold]+[{**row,'label_origin':'AI_synthetic_user_accepted','sample_weight':cfg['synthetic_loss_weight']} for row in synth]
    source_paths={'gold_train':train_path,'validation':val_path,'test_text_only':test_path,'synthetic_manifest':manifest_path,'synthetic_train':synth_dir/('train_comments.csv' if genz else 'train.jsonl')}
    if genz:source_paths['synthetic_development']=synth_dir/'development_threads.jsonl'
    sources={name:{'path':str(path),'sha256':file_hash(path)} for name,path in source_paths.items()}
    fingerprint=file_hash(config_path)+':'+file_hash(base/'model.safetensors')+':'+json.dumps(sources,sort_keys=True)
    if (output/'manifest.json').exists():
        previous=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
        if previous['fingerprint']!=fingerprint or any(file_hash(output/name)!=sha for name,sha in previous['output_sha256'].items()):raise FileExistsError('Prepared version differs; never overwrite')
        return previous
    if output.exists() and any(output.iterdir()):raise FileExistsError('Choose an empty preparation output')
    output.mkdir(parents=True,exist_ok=True)
    for name,items in [('train.jsonl',rows),('validation.jsonl',validation)]:
        (output/name).write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in items),encoding='utf-8')
    gate=json.loads(resolve(root,cfg['independent_evaluation_manifest']).read_text(encoding='utf-8'))
    protocol=cfg.get('evaluation_protocol','real_independent')
    report={'evaluation_protocol':protocol,'development_challenge_comments':len(challenge),'status':'PREPARED_NOT_TRAINED','task_status':'BLOCKED','blockers':(['Bounded local CPU authorization not yet checked'] if cfg.get('training_strategy')=='frozen_encoder_head_cpu' else (['T028 independent real evaluation not complete'] if protocol=='real_independent' else [])+['G3 exact config/resource approval not recorded; local CUDA unavailable']),
      'config_sha256':file_hash(config_path),'fingerprint':fingerprint,'base_model_path':str(base),'base_model_sha256':file_hash(base/'model.safetensors'),
      'threshold':.41,'gold_train_rows':len(gold),'synthetic_train_rows':len(synth),'total_train_rows':len(rows),'synthetic_fraction':ratio,
      'labels':dict(Counter(row['label'] for row in rows)),'synthetic_input_rows':len(original_synth),'excluded_uncertain':synth_manifest['excluded_uncertain'],
      'cleanup':{'gold_exact':clean,'gold_near_heldout_removed':len(near_gold),'synthetic_exact':synth_clean,'synthetic_near_heldout_removed':len(near_synth),
        'synthetic_gold_exact_removed':len(overlaps),'synthetic_gold_near_removed':len(near_cross)},
      'sources':sources,'heldout_modified':False,'test_labels_used':False,'test_predictions_generated':False,'training_performed':False,
      'T028_manifest_status':gate.get('status'),'T028_data_files':len(gate.get('data_files',[])),
      'independent_blind_evaluation_ready':False,'approval_recorded':False,
      'output_sha256':{name:file_hash(output/name) for name in ('train.jsonl','validation.jsonl')},
      'similarity_scope':{'normalization':'NFC/casefold/space for comparison only','char5_jaccard':cfg['near_duplicate_threshold'],'min_chars':cfg['near_duplicate_min_chars']},
      'limitations':['Historical ViCTSD holdouts are not the missing T028 independent real benchmark.','AI labels remain synthetic, not human gold.','Character similarity cannot rule out all semantic paraphrases.']}
    atomic_json(output/'manifest.json',report)
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=ROOT/'configs/t029_candidate.json');p.add_argument('--output',type=Path,default=ROOT/'reports/ai_update/T029/prepared');p.add_argument('--base-model',type=Path,required=True);a=p.parse_args()
    report=prepare(a.config,a.output,a.base_model)
    print(json.dumps({k:report[k] for k in ('status','task_status','gold_train_rows','synthetic_train_rows','total_train_rows','synthetic_fraction','cleanup','blockers')},ensure_ascii=True))
if __name__=='__main__':main()
