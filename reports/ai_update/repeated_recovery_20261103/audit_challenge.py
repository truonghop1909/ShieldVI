"""Post-score integrity/novelty audit, never changes text, labels or rules."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;D=R/'datasets/fixtures/repeated_holdout_20261103'
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import file_sha,atomic_json,grams,normalized
from real_dataset.leakage import development_index
m=json.loads((D/'manifest.json').read_text(encoding='utf-8'));lock=json.loads((P/'frozen_rule_lock.json').read_text())
assert all(file_sha(R/'services/moderation-ai/app'/name)==h for name,h in lock['rule_sha256'].items())
threads=[]
for tid,h in m['thread_sha256'].items():
    p=D/(tid+'.json');assert file_sha(p)==h;threads.append(json.loads(p.read_text(encoding='utf-8')))
texts=[c['text'] for t in threads for c in t['comments']]
sources=list((R/'datasets/synthetic_genz/threads').glob('*.json'))+list((R/'datasets/fixtures/context_recovery_v1/threads').glob('*.json'))+list((R/'datasets/fixtures/genz_regression').glob('*.json'))
prior=[c['text'] for p in sources for c in json.loads(p.read_text(encoding='utf-8'))['comments']]
norm=[normalized(x) for x in texts];old={normalized(x) for x in prior}
assert len(set(norm))==len(norm) and not set(norm)&old
shapes=[(x,grams(x)) for x in prior if len(normalized(x))>=35];near=[];maxima=[]
for text in texts:
    if len(normalized(text))<35:continue
    g=grams(text);maximum=0
    for previous,h in shapes:
        if min(len(g),len(h))/max(len(g),len(h))<.85:continue
        similarity=len(g&h)/len(g|h);maximum=max(maximum,similarity)
        if similarity>=.85:near.append({'new':text,'existing':previous,'similarity':similarity})
    maxima.append(maximum)
if near:raise ValueError('Fresh challenge has near duplicate overlap; report without pretending fresh')
path=R/'datasets/real_conversations/manifests/development_exclusions.json'
manifest=json.loads(path.read_text(encoding='utf-8'))
if not (P/'development_exclusions.before.json').exists():atomic_json(P/'development_exclusions.before.json',manifest)
existing={x['path'] for x in manifest['source_records']}
for t in threads:
    p=D/(t['thread_id']+'.json');name=p.relative_to(R).as_posix()
    if name not in existing:manifest['source_records'].append({'path':name,'sha256':file_sha(p),'format':'thread_json'})
atomic_json(path,manifest)
ids,_,groups=development_index(R/'datasets/real_conversations',R)
assert all(t['thread_id'] in ids and len(groups[t['thread_id']])==len(t['comments']) for t in threads)
atomic_json(P/'fresh_audit.json',{'status':'PASS','threads':len(threads),'comments':len(texts),'exact_duplicates':0,'exact_overlap_existing':0,
    'near_overlap_existing':len(near),'char5_jaccard_threshold':.85,'min_chars':35,
    'no_post_score_rule_changes':True,'fresh_manifest_sha256':file_sha(D/'manifest.json'),
    'all12_registered_as_excluded_from_independent_real_cohort':True,'human_gold':False,'semantic_novelty_proven':False})
print(json.dumps({'status':'PASS','fresh_threads':12,'comments':len(texts),'near_overlap':len(near),'rule_changes_after_scoring':0}))
