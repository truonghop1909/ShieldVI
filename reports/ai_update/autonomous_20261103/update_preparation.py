from pathlib import Path
import json
p=Path('scripts/synthetic_data/genz.py')
s=p.read_text(encoding='utf-8')
needle='def checkpoint(through=500,seed=20261103,output=DATA):'
insert='''def verified_export(directory=DATA):
    """Recompute eligibility from immutable records, not a user-edited READY flag."""
    directory=Path(directory);manifest=json.loads((directory/'dataset_manifest.json').read_text(encoding='utf-8'))
    if manifest['threads']!=500 or manifest['data_origin']!='synthetic' or manifest['human_gold'] is not False:
        raise ValueError('Expected complete AI-only GenZ500 version')
    for name,sha in manifest['output_sha256'].items():
        if old.file_sha(directory/name)!=sha:raise ValueError('GenZ output checksum mismatch: '+name)
    threads=[]
    for tid,sha in manifest['thread_sha256'].items():
        path=directory/'threads'/(tid+'.json')
        if old.file_sha(path)!=sha:raise ValueError('GenZ thread checksum mismatch: '+tid)
        threads.append(Thread.model_validate_json(path.read_text(encoding='utf-8')).model_dump(mode='json'))
    report=validate(threads)
    if report['status']!='PASS':raise ValueError('GenZ validation failed')
    expected=[]
    for t in threads:
        for c in t['comments']:
            a=c['annotation']
            if t['split']=='train' and a['label']!='UNCERTAIN' and not a['needs_human_review']:
                expected.append((t['thread_id'],c['comment_id'],c['text'],str(int(a['label']=='TOXIC'))))
    with (directory/'train_comments.csv').open(encoding='utf-8-sig',newline='') as f:
        actual=[(r['thread_id'],r['comment_id'],r['Comment'],r['Toxicity']) for r in csv.DictReader(f)]
    if expected!=actual:raise ValueError('Training CSV disagrees with eligible authored annotations')
    challenge=[t for t in threads if t['split']=='development_challenge']
    if not challenge:raise ValueError('Missing separate development challenge')
    stored=[json.loads(line) for line in (directory/'development_threads.jsonl').read_text(encoding='utf-8').splitlines()]
    if stored!=challenge:raise ValueError('Challenge export differs from thread records')
    return manifest,threads,report

'''
assert needle in s;s=s.replace(needle,insert+needle);p.write_text(s,encoding='utf-8')
p=Path('scripts/prepare_t029_training.py');s=p.read_text(encoding='utf-8')
s=s.replace("    return config\n", "    if config.get('evaluation_protocol','real_independent') not in ('real_independent','synthetic_development'):raise ValueError('Unknown evaluation protocol')\n    return config\n",1)
s=s.replace("    synth_dir=resolve(root,cfg['synthetic_export']);synth_manifest=json.loads((synth_dir/'manifest.json').read_text(encoding='utf-8'))", """    synth_dir=resolve(root,cfg['synthetic_export']);genz=cfg.get('synthetic_format')=='genz_v2'
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
        original_synth=[json.loads(line) for line in (synth_dir/'train.jsonl').read_text(encoding='utf-8').splitlines()]""")
s=s.replace("heldout=[row['text'] for row in validation+test_text]","heldout=[row['text'] for row in validation+test_text]+challenge")
s=s.replace("    original_synth=[json.loads(line) for line in (synth_dir/'train.jsonl').read_text(encoding='utf-8').splitlines()]\n    synth=[]","    synth=[]")
s=s.replace("'synthetic_manifest':synth_dir/'manifest.json','synthetic_train':synth_dir/'train.jsonl'", "'synthetic_manifest':manifest_path,'synthetic_train':synth_dir/('train_comments.csv' if genz else 'train.jsonl')")
s=s.replace("    sources={name:","    if genz:source_paths['synthetic_development']=synth_dir/'development_threads.jsonl'\n    sources={name:",1)
s=s.replace("    report={'status':", "    protocol=cfg.get('evaluation_protocol','real_independent')\n    report={'evaluation_protocol':protocol,'development_challenge_comments':len(challenge),'status':",1)
s=s.replace("'blockers':['T028 independent real evaluation not complete','G3 exact config/resource approval not recorded']", "'blockers':(['T028 independent real evaluation not complete'] if protocol=='real_independent' else [])+['G3 exact config/resource approval not recorded; local CUDA unavailable']")
p.write_text(s,encoding='utf-8')
p=Path('scripts/train_t029_candidate.py');s=p.read_text(encoding='utf-8')
start=s.index('    # G2 must come');end=s.index('\n    receipt=',start)
block=s[start:end]
# Preserve original real-world eligibility branch; synthetic research has its own verified data check.
new='''    protocol=cfg.get('evaluation_protocol','real_independent')
    if protocol=='synthetic_development':
        from synthetic_data.genz import verified_export
        from prepare_t029_training import remove_near
        from refine_model import clean_train
        try:
            _,threads,_=verified_export(resolve(root,cfg['synthetic_export']))
            dev=[c['text'] for t in threads if t['split']=='development_challenge' for c in t['comments']]
            train=[json.loads(line) for line in (prepared/'train.jsonl').read_text(encoding='utf-8').splitlines()]
            isolated,exact=clean_train(train,dev)
            _,near=remove_near(isolated,dev,cfg['near_duplicate_threshold'],cfg['near_duplicate_min_chars'])
            if exact['overlap_removed'] or near:blocked.append('G2-S: training overlaps development challenge')
            if info.get('evaluation_protocol')!=protocol:blocked.append('G2-S: prepared protocol mismatch')
        except (ValueError,KeyError,OSError):blocked.append('G2-S: synthetic source eligibility failed')
    else:
'''+''.join('    '+line+'\n' for line in block.splitlines())
s=s[:start]+new.rstrip()+s[end:];p.write_text(s,encoding='utf-8')
cfg=json.loads(Path('configs/t029_candidate.json').read_text(encoding='utf-8'))
cfg.update(run_id='T029_genz500_20261103_r02',output_dir='/content/drive/MyDrive/shieldvi_candidates/T029_genz500_20261103_r02',synthetic_export='datasets/synthetic_conversations/genz_v2',synthetic_format='genz_v2',evaluation_protocol='synthetic_development',max_synthetic_fraction=.40,estimated_cost='Unknown; CUDA runtime and exact cost still require approval; no CPU fine-tune')
Path('configs/t029_genz500_candidate.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
base=Path('datasets/synthetic_conversations/genz_v2');m=json.loads((base/'dataset_manifest.json').read_text(encoding='utf-8'))
(base/'README.md').write_text('''# GenZ v2 — AI-authored synthetic data

500 conversations / 5,115 comments. REAL=0; human gold=0. 200 legacy conversations (2,048 comments) imported with unchanged text and source SHA; 300 newly authored conversations (3,067 comments) compiled from six explicit Codex catalogues. No external generation API, no scraped conversation, no template-based language generation. Deterministic Python compiles schema, IDs, timestamps, category mapping and exports; profanity flags are heuristic and never assign toxicity.

- `threads/`: all 500 annotated JSONs. `dashboard_threads/`: the corresponding API-clean inputs (no label or persona leakage).
- `train_comments.csv`: 4,398 eligible binary rows. `train_threads.jsonl`: 440 training threads with complete annotations, including uncertain rows (filter before loss).
- `development_threads.jsonl`: 60 newly authored challenge threads, grouped by scenario family, not real blind evaluation.
- `labels_review.csv`: AI references with blank human-label column; no manual review is claimed. UNCERTAIN/review-flagged targets are excluded from the binary training CSV.
- `dataset_manifest.json`: hashes, provenance and checkpoint. `batches/`: four imported blocks of50 and seven new checkpoints (20,30,50×5); 11 successful batch manifests. `rejected_validation.json` records a historical rejected attempt at450, corrected before export; it is not a completed batch.
- Run from repository root: `.\\.venv\\Scripts\\python.exe -X utf8 scripts/generate_genz_dataset.py --through 500` (idempotent; refuses changed existing threads). Source catalogue: `scripts/synthetic_data/genz_catalogue/`.

## Annotation and limitations

Labels CLEAN/TOXIC/UNCERTAIN are synthetic suggestions accepted for research, not human gold. `category` is the six-class requested taxonomy; `semantic_role` retains the finer authoring intent. `target_evidence` quotes the actual authored utterance; this is AI evidence, not independent confirmation. Repeated flags require earlier same-actor/same-target attacks with IDs, distinct timestamps. Neutral parent links never imply an attack target.

`needs_human_review` is an annotation uncertainty flag; it does not require the user to relabel the entire synthetic set. Optional reviews must be stored separately and never fabricated. Names A–F and timestamps are fictional.

The catalogue is directly authored, but many examples have short, explicit discourse and a compact attack/response structure. Most threads are near the 10-comment minimum. Technical checks (character5 Jaccard, limited synonym delexicalization, role sequence frequency) cannot establish semantic novelty, naturalness or annotation accuracy. CLEAN dominates (4,667 /5,115); do not claim balanced training or real-world generalization. English/obfuscation coverage counters are heuristic and may undercount. Topic aliases refer to 15 broad domains; sports includes football. No model has been trained on this version in this session.

Use separate historical ViCTSD validation for model selection and immutable test only for a final audit. Training preparation also excludes exact/near matches to challenge and held-outs. Do not treat this development split as an independent test or use the original200 trained/development examples as new held-out evidence.
''',encoding='utf-8')
print('GenZ verified loader, research-specific preparation/gate and versioned candidate config written')
