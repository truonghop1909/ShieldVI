"""Export user-accepted AI labels as synthetic training data, never human gold."""
import csv,json
from collections import Counter
from pathlib import Path
from .pipeline import DATA,Thread,validate,atomic_json,file_sha

OUTPUT=DATA/'training_ai_labels_v1'

def export(data_root=DATA,output=OUTPUT):
    root=Path(data_root);output=Path(output)
    source_manifest=root/'manifest.json';manifest=json.loads(source_manifest.read_text(encoding='utf-8'))
    threads=[]
    for path in sorted((root/'threads').glob('*.json')):
        t=Thread.model_validate(json.loads(path.read_text(encoding='utf-8'))).model_dump(mode='json')
        if path.name!=t['thread_id']+'.json' or file_sha(path)!=manifest['thread_checksums'].get(t['thread_id']):raise ValueError('Source checksum mismatch')
        threads.append(t)
    if {t['thread_id'] for t in threads}!=set(manifest['thread_checksums']) or len(threads)!=manifest['actual_threads']:raise ValueError('Source inventory mismatch')
    report=validate(threads)
    if report['status']!='PASS':raise ValueError('Source quality validation failed')
    source_sha=file_sha(source_manifest)
    if (output/'manifest.json').exists():
        prior=json.loads((output/'manifest.json').read_text(encoding='utf-8'))
        if prior['source_manifest_sha256']!=source_sha:raise FileExistsError('Use a new export version for changed source')
        for name,sha in prior['output_sha256'].items():
            if file_sha(output/name)!=sha:raise FileExistsError('Existing export edited; never overwrite')
        return prior
    if output.exists() and any(output.iterdir()):raise FileExistsError('Export folder must be empty; do not overwrite')
    output.mkdir(parents=True,exist_ok=True)
    train=[];uncertain=[]
    for t in threads:
        for c in t['comments']:
            a=c['annotation']
            record={'thread_id':t['thread_id'],'topic':t['topic'],'comment_id':c['comment_id'],'parent_id':c['parent_id'],
              'user_id':c['user_id'],'timestamp':c['timestamp'],'text':c['text'],'comment_label':a['label'],
              'data_origin':'synthetic','label_source':'synthetic','review_status':'AI_REFERENCE_ACCEPTED_BY_USER',
              'manual_review_performed':False,'human_gold':False,'evaluation_eligible':False,
              'source_file':'threads/'+t['thread_id']+'.json','source_sha256':manifest['thread_checksums'][t['thread_id']],
              'context_annotation':a}
            if a['label']=='UNCERTAIN':
                record.update(exclusion_reason='UNCERTAIN has no binary training label; kept unchanged, not mapped to CLEAN')
                uncertain.append(record)
            else:
                record.update(label=1 if a['label']=='TOXIC' else 0,split='train')
                train.append(record)
    for filename,rows in [('train.jsonl',train),('excluded_uncertain.jsonl',uncertain)]:
        (output/filename).write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
    with (output/'train.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        fields=['thread_id','comment_id','Comment','Toxicity','label_source','review_status','data_origin'];writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in train:writer.writerow({'thread_id':row['thread_id'],'comment_id':row['comment_id'],'Comment':row['text'],'Toxicity':row['label'],
          'label_source':'synthetic','review_status':row['review_status'],'data_origin':'synthetic'})
    result={'status':'PREPARED_AI_LABELED_SYNTHETIC_TRAINING_DATA','source_threads':len(threads),'source_comments':report['comments'],
      'training_rows':len(train),'excluded_uncertain':len(uncertain),'labels':dict(Counter(row['comment_label'] for row in train)),
      'label_mapping':{'CLEAN':0,'TOXIC':1},'data_origin':'synthetic','label_source':'synthetic','human_gold':False,
      'manual_review_performed':False,'manual_review_required_for_this_export':False,
      'label_use_decision':'User explicitly requested using the existing AI labels without manual annotation.',
      'evaluation_eligible':False,'validation_or_test_created':False,'training_performed':False,
      'source_manifest_sha256':source_sha,'output_sha256':{name:file_sha(output/name) for name in ('train.jsonl','train.csv','excluded_uncertain.jsonl')},
      'limitations':['AI reference labels can be incorrect; technical validation is not human verification.',
        'Only a synthetic augmentation source; original training data is not replaced or merged automatically.',
        'Labels/context metadata must not be concatenated into classifier text input.',
        'Some parent comments are UNCERTAIN and excluded from binary targets; full context remains in source threads.']}
    atomic_json(output/'manifest.json',result)
    (output/'README.md').write_text('AI-labeled synthetic training augmentation accepted by user. Not human gold. See manifest.json. No training performed.'+chr(10),encoding='utf-8')
    return result
