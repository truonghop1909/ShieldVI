"""Versioned three-way synthetic view and pure-synthetic preparation; no new prose."""
import copy,csv,json,math,hashlib
from collections import Counter,defaultdict
from pathlib import Path
from .pipeline import atomic_json,file_sha
from .genz import verified_export
ROOT=Path(__file__).resolve().parents[2]

def split_families(threads,seed):
    roles={t['scenario_family']:'synthetic_train' for t in threads if t['split']=='train'}
    groups=defaultdict(list)
    for t in threads:
        if t['split']=='development_challenge':
            labels={c['annotation']['label'] for c in t['comments']}
            groups[('TOXIC' in labels,'UNCERTAIN' in labels)].append(t['scenario_family'])
    rank=lambda family:hashlib.sha256((str(seed)+'|'+family).encode()).hexdigest()
    validation=[];challenge=[]
    for values in groups.values():
        values=sorted(set(values),key=rank);middle=len(values)//2
        validation+=values[:middle];challenge+=values[middle:]
    target=(len(validation)+len(challenge))//2
    while len(validation)<target:
        family=min(challenge,key=rank);challenge.remove(family);validation.append(family)
    if set(roles)&(set(validation)|set(challenge)):raise ValueError('Existing family leakage')
    roles.update({f:'synthetic_validation' for f in validation});roles.update({f:'synthetic_challenge' for f in challenge})
    return roles

def flattened(thread,role,source_sha):
    t=copy.deepcopy(thread);t['original_split']=t['split'];t['split']=role;t['canonical_thread_sha256']=source_sha
    t['human_gold']=False;t['comments']=[{**{k:v for k,v in c.items() if k!='annotation'},'thread_id':t['thread_id'],**c['annotation']} for c in t['comments']]
    return t

def export_dataset(output,source=None,seed=20261103,progress=None):
    output=Path(output);source=Path(source or ROOT/'datasets/synthetic_conversations/genz_v2')
    m,threads,quality=verified_export(source)
    if (output/'dataset_manifest.json').exists():
        verify_view(output,source);return json.loads((output/'dataset_manifest.json').read_text(encoding='utf-8'))
    roles=split_families(threads,seed);view=[flattened(t,roles[t['scenario_family']],m['thread_sha256'][t['thread_id']]) for t in threads]
    output.mkdir(parents=True,exist_ok=True);(output/'threads').mkdir(exist_ok=True);(output/'batches').mkdir(exist_ok=True)
    ends=[20]+list(range(70,500,50))+[500];start=0
    for end in ends:
        batch=view[start:end]
        for t in batch:
            p=output/'threads'/(t['thread_id']+'.json')
            if p.exists() and json.loads(p.read_text(encoding='utf-8'))!=t:raise FileExistsError('Refuse different existing thread '+t['thread_id'])
            if not p.exists():atomic_json(p,t)
        record={'start':start+1,'end':end,'threads':len(batch),'cumulative_threads':end,'status':'VALIDATED_REUSED_SOURCE',
          'new_utterances_generated':0,'human_gold':False,'thread_sha256':{t['thread_id']:file_sha(output/'threads'/(t['thread_id']+'.json')) for t in batch}}
        bp=output/'batches'/f'batch_{end:04d}.json'
        if bp.exists() and json.loads(bp.read_text(encoding='utf-8'))!=record:raise FileExistsError('Batch differs')
        if not bp.exists():atomic_json(bp,record)
        if progress:progress(end,record)
        start=end
    fields=['thread_id','comment_id','parent_id','user_id','timestamp','text','label','category','directed_at_user_id','has_profanity','is_directed_attack','is_repeated_attack','is_apology','is_quote','label_reason','label_source','needs_human_review','evidence_comment_ids','scenario_family','split']
    allrows=[{**c,'scenario_family':t['scenario_family'],'split':t['split']} for t in view for c in t['comments']]
    exports={
      'train_comments.csv':[r for r in allrows if r['split']=='synthetic_train' and r['label']!='UNCERTAIN' and not r['needs_human_review']],
      'validation_comments.csv':[r for r in allrows if r['split']=='synthetic_validation'],
      'challenge_comments.csv':[r for r in allrows if r['split']=='synthetic_challenge'],'labels_review.csv':allrows}
    for name,rows in exports.items():
        columns=fields+(['human_label'] if name=='labels_review.csv' else [])
        with (output/name).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');writer.writeheader()
            for row in rows:writer.writerow({**row,'evidence_comment_ids':json.dumps(row['evidence_comment_ids']),'human_label':''}) if name=='labels_review.csv' else writer.writerow({**row,'evidence_comment_ids':json.dumps(row['evidence_comment_ids'])})
    for role,name in [('synthetic_train','train_threads.jsonl'),('synthetic_validation','validation_threads.jsonl'),('synthetic_challenge','challenge_threads.jsonl')]:
        (output/name).write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in view if t['split']==role),encoding='utf-8')
    split={'seed':seed,'roles_by_family':roles,'roles_by_thread':{t['thread_id']:t['split'] for t in view},
      'source_roles_preserved':True,'original_development_role_refined_only_in_new_view':True,
      'selection':'Family/label strata only, before candidate inference; no model score used','independent_evaluation':False,
      'known_development_warning':'Original holdouts were already used for rules/research; neither derived validation nor challenge is blind or human gold.'}
    atomic_json(output/'split_manifest.json',split)
    result={'status':'COMPLETE_EXPERIMENTAL_SYNTHETIC_VIEW','threads':len(view),'comments':len(allrows),'labels':dict(Counter(r['label'] for r in allrows)),
      'data_origin':'synthetic','label_source':'synthetic','human_gold':False,'new_utterances_generated':0,'reused_threads':500,
      'canonical_source':str(source.resolve()),'canonical_manifest_sha256':file_sha(source/'dataset_manifest.json'),
      'splits':dict(Counter(t['split'] for t in view)),'family_roles':roles,'training_binary_rows':len(exports['train_comments.csv']),
      'human_review_flags':sum(r['needs_human_review'] for r in allrows),'source_quality':quality,
      'thread_sha256':{t['thread_id']:file_sha(output/'threads'/(t['thread_id']+'.json')) for t in view},
      'output_sha256':{p.name:file_sha(p) for p in output.iterdir() if p.suffix in ('.csv','.jsonl') or p.name=='split_manifest.json'},
      'generation':'Reused prior Codex-authored catalogue with deterministic schema compilation; no new LLM/API/template prose generated this run.',
      'limitations':['AI reference labels, not human gold.','Reuse/role statistics and character similarity cannot prove semantic novelty or naturalness.','Legacy scenario structure recurs; no claim of500fully independent scripts.','Real T028 remains blocked.']}
    atomic_json(output/'dataset_manifest.json',result)
    (output/'quality_report.md').write_text('# Experimental synthetic quality\n\n'+json.dumps({k:result[k] for k in ('threads','comments','labels','splits','human_review_flags','training_binary_rows')},ensure_ascii=False,indent=2)+'\n\nSource schema, parents, times, participants, duplicates/near-duplicates and family split recomputed by existing GenZ validator. Utterances/AI labels exactly preserved in this derived view. Source quality statistics: '+json.dumps(quality,ensure_ascii=False)+'\n\nSemantic novelty/naturalness is not established by these automatic checks; review flags are not human review.\n',encoding='utf-8')
    (output/'README.md').write_text('# Synthetic GenZ experimental view\n\n500reused threads/5115comments from ../synthetic_conversations/genz_v2, with unchanged text/AI references and flat comment fields. No real data, no human gold. This is a versioned three-way export, not a claim of500newly generated dialogues. Old canonical files/splits remain immutable.\n\nthreads/ contains all500JSONs; batches/ records pilot20 then50-sized validated reuse batches. train_comments.csv excludes UNCERTAIN/review-flagged rows. labels_review.csv retains all labels and an empty human_label column. validation/challenge are source-held-out development families, already seen in rule research; never call them blind or independent evaluation. Original training families remain train so r05does not train on the new validation/challenge inputs. Source checksums/split manifest bind lineage. No model predictions are mixed into these files.\n',encoding='utf-8')
    return result

def verify_view(directory,source=None):
    directory=Path(directory);manifest=json.loads((directory/'dataset_manifest.json').read_text(encoding='utf-8'))
    source=Path(source or manifest['canonical_source']);m,threads,report=verified_export(source)
    if manifest['canonical_manifest_sha256']!=file_sha(source/'dataset_manifest.json') or manifest['human_gold'] is not False:raise ValueError('Invalid synthetic lineage')
    if len(manifest['thread_sha256'])!=500:raise ValueError('Expected500threads')
    byid={t['thread_id']:t for t in threads};view=[]
    for tid,sha in manifest['thread_sha256'].items():
        p=directory/'threads'/(tid+'.json')
        if file_sha(p)!=sha:raise ValueError('Derived thread changed')
        t=json.loads(p.read_text(encoding='utf-8'));expected=flattened(byid[tid],manifest['family_roles'][byid[tid]['scenario_family']],m['thread_sha256'][tid])
        if t!=expected:raise ValueError('Derived text/label/split differs from canonical source')
        view.append(t)
    for name,sha in manifest['output_sha256'].items():
        if file_sha(directory/name)!=sha:raise ValueError('Derived export changed: '+name)
    return manifest,view,report

def prepare(config_path,output,base_model,root=ROOT):
    from prepare_t029_training import validate_config,remove_near
    from refine_model import clean_train
    root=Path(root);output=Path(output);base=Path(base_model).resolve();config_path=Path(config_path)
    cfg=validate_config(json.loads(config_path.read_text(encoding='utf-8')));directory=root/cfg['experimental_dataset']
    manifest,threads,_=verify_view(directory,root/cfg['synthetic_export'])
    if json.loads((base/'threshold_config.json').read_text(encoding='utf-8'))['threshold']!=.41:raise ValueError('Threshold mismatch')
    if output.exists() and any(output.iterdir()):raise FileExistsError('Choose new prepared output')
    train=[];validation=[];heldout=[]
    for t in threads:
        for c in t['comments']:
            if t['split']!='synthetic_train':heldout.append(c['text'])
            if c['label']=='UNCERTAIN' or (t['split']=='synthetic_train' and c['needs_human_review']):continue
            row={'id':t['thread_id']+':'+c['comment_id'],'thread_id':t['thread_id'],'comment_id':c['comment_id'],'text':c['text'],
                 'label':int(c['label']=='TOXIC'),'label_origin':'AI_synthetic_user_accepted','label_source':'synthetic','human_gold':False}
            if t['split']=='synthetic_train':train.append(row)
            elif t['split']=='synthetic_validation':validation.append(row)
    # Known rule-development fixtures stay outside training and are never independent test data.
    regression_sources=list((root/'datasets/fixtures/genz_regression').glob('*.json'))+list((root/'datasets/fixtures/context_recovery_v1/dashboard_threads').glob('*.json'))
    for p in regression_sources:heldout.extend(c['text'] for c in json.loads(p.read_text(encoding='utf-8'))['comments'])
    original=len(train);train,cleanup=clean_train(train,heldout);train,near=remove_near(train,heldout,cfg['near_duplicate_threshold'],cfg['near_duplicate_min_chars'])
    counts=Counter(r['label'] for r in train)
    if not counts[0] or not counts[1] or not validation:raise ValueError('Both training classes and validation required')
    positive=min(4.,math.sqrt(counts[0]/counts[1]))
    for row in train:row['sample_weight']=positive if row['label'] else 1.
    output.mkdir(parents=True)
    for name,rows in [('train.jsonl',train),('validation.jsonl',validation)]:
        (output/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    paths={'canonical_manifest':root/cfg['synthetic_export']/'dataset_manifest.json','experimental_manifest':directory/'dataset_manifest.json',
       'split_manifest':directory/'split_manifest.json','synthetic_train':directory/'train_comments.csv','synthetic_validation':directory/'validation_comments.csv','synthetic_challenge':directory/'challenge_comments.csv'}
    paths.update({'regression_'+str(i):path for i,path in enumerate(regression_sources)})
    info={'status':'PREPARED_EXPERIMENTAL_SYNTHETIC_ONLY','evaluation_protocol':'synthetic_development','data_recipe':'synthetic_only',
      'config_sha256':file_sha(config_path),'base_model_path':str(base),'base_model_sha256':file_sha(base/'model.safetensors'),
      'threshold':.41,'gold_train_rows':0,'synthetic_train_rows':len(train),'total_train_rows':len(train),'validation_rows':len(validation),
      'synthetic_fraction':1.,'training_input_rows':original,'cleanup':cleanup,'near_heldout_exclusions':[r['id'] for r in near],
      'training_class_counts':dict(counts),'positive_sample_weight':positive,'class_weight_policy':'sqrt(clean/toxic), capped4; class weights apply to CE+distillation',
      'sources':{name:{'path':str(path.resolve()),'sha256':file_sha(path)} for name,path in paths.items()},
      'output_sha256':{name:file_sha(output/name) for name in ('train.jsonl','validation.jsonl')},'human_gold':False,
      'real_training_used':False,'independent_real_ready':False,'training_performed':False,'test_labels_used':False,'test_predictions_generated':False}
    atomic_json(output/'manifest.json',info);return info

def verify_prepared(config,prepared,root=ROOT):
    directory=Path(root)/config['experimental_dataset'];_,threads,_=verify_view(directory,Path(root)/config['synthetic_export'])
    expected={t['thread_id']+':'+c['comment_id']:(t,c) for t in threads for c in t['comments']}
    for name,role in [('train.jsonl','synthetic_train'),('validation.jsonl','synthetic_validation')]:
        for line in (Path(prepared)/name).read_text(encoding='utf-8').splitlines():
            r=json.loads(line);t,c=expected[r['id']]
            if t['split']!=role or c['label']=='UNCERTAIN' or (role=='synthetic_train' and c['needs_human_review']):raise ValueError('Invalid synthetic eligibility')
            if r['text']!=c['text'] or r['label']!=int(c['label']=='TOXIC') or r['human_gold'] is not False:raise ValueError('Training reference changed')
