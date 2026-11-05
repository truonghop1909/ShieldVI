"""Local, fail-closed review ingestion. Never trains or changes original datasets."""
import hashlib,json,re,unicodedata
from collections import Counter,defaultdict
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SEED='20261102'
NEAR_THRESHOLD=.9

def normalized(text):return re.sub(r'\s+',' ',unicodedata.normalize('NFC',text).casefold()).strip()
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def grams(text):return {text[i:i+5] for i in range(max(1,len(text)-4))}
def eligible(row):
    return bool(row.get('approved_for_training') is True and row.get('license_approved') is True and row.get('review_status')=='VERIFIED_SOLO' and row.get('human_label') in ('CLEAN','TOXIC') and row.get('split')!='development_regression')

def prepare(rows,output,source_manifest=None):
    output=Path(output)
    input_hash=hashlib.sha256(json.dumps(rows,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    fingerprint=hashlib.sha256((input_hash+json.dumps(source_manifest or {},sort_keys=True)).encode()).hexdigest()
    if (output/'dataset_manifest.json').exists():
        prior=json.loads((output/'dataset_manifest.json').read_text(encoding='utf-8'))
        if prior['fingerprint']==fingerprint:return prior
        raise FileExistsError('Use a new dataset version; never overwrite reviewer edits')
    if output.exists() and any(output.iterdir()):raise FileExistsError('Output directory must be empty')
    output.mkdir(parents=True,exist_ok=True)
    accepted=[];rejected=[];keys=set();bad_threads=set();lookup={}
    for row in rows:
        try:
            key=(row['thread_id'],row['comment_id'])
            if key in keys:raise ValueError('duplicate_id')
            keys.add(key)
            if not isinstance(row['raw_text'],str) or not row['raw_text'].strip():raise ValueError('empty_text')
            stamp=datetime.fromisoformat(row['timestamp'].replace('Z','+00:00'))
            if stamp.utcoffset() is None:raise ValueError('timezone_required')
            if not row.get('source_id') or not row.get('source_type'):raise ValueError('missing_provenance')
            copy=dict(row);copy['normalized_text']=normalized(row['raw_text']);accepted.append(copy);lookup[key]=copy
        except (ValueError,KeyError,TypeError) as exc:
            bad_threads.add(row.get('thread_id'))
            rejected.append({'thread_id':row.get('thread_id'),'comment_id':row.get('comment_id'),'reason':str(exc)})
    for row in accepted:
        parent=row.get('parent_id');seen={row['comment_id']}
        while parent:
            key=(row['thread_id'],parent)
            if key not in lookup or parent in seen:
                bad_threads.add(row['thread_id']);break
            seen.add(parent);p=lookup[key]
            if datetime.fromisoformat(p['timestamp'].replace('Z','+00:00'))>datetime.fromisoformat(row['timestamp'].replace('Z','+00:00')):
                bad_threads.add(row['thread_id'])
            parent=p.get('parent_id')
    valid=[]
    for row in accepted:
        if row['thread_id'] in bad_threads:rejected.append({'thread_id':row['thread_id'],'comment_id':row['comment_id'],'reason':'invalid_thread_context'})
        else:valid.append(row)
    # Union entire threads on exact and near-duplicate content, before splitting.
    parents={row['thread_id']:row['thread_id'] for row in valid}
    def find(x):
        while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parents[max(a,b)]=min(a,b)
    text_groups=defaultdict(list)
    for row in valid:text_groups[row['normalized_text']].append(row)
    for group in text_groups.values():
        for row in group[1:]:union(group[0]['thread_id'],row['thread_id'])
    unique=list(text_groups);signatures={s:grams(s) for s in unique};near_edges=0
    for i,a in enumerate(unique):
        for b in unique[i+1:]:
            ga,gb=signatures[a],signatures[b]
            if min(len(ga),len(gb))/max(len(ga),len(gb))<NEAR_THRESHOLD:continue
            if len(ga&gb)/len(ga|gb)>=NEAR_THRESHOLD:
                union(text_groups[a][0]['thread_id'],text_groups[b][0]['thread_id']);near_edges+=1
    forced_train={find(row['thread_id']) for row in valid if row.get('used_in_prior_training')}
    partitions={'train':[],'validation':[],'test':[]};seen_export=set()
    for row in valid:
        component=find(row['thread_id']);row['leakage_group']=component
        row['training_eligible']=eligible(row)
        if not row['training_eligible']:continue
        key=(row['normalized_text'],row['human_label'])
        if key in seen_export:continue
        seen_export.add(key)
        bucket=int(hashlib.sha256((SEED+component).encode()).hexdigest(),16)%10
        split='train' if component in forced_train or bucket>=2 else 'validation' if bucket==1 else 'test'
        partitions[split].append(row)
    # Conflicting verified labels invalidate export rather than select one silently.
    labels=defaultdict(set)
    for row in valid:
        if eligible(row):labels[row['normalized_text']].add(row['human_label'])
    conflicts={s for s,v in labels.items() if len(v)>1}
    for split in partitions:partitions[split]=[r for r in partitions[split] if r['normalized_text'] not in conflicts]
    def jsonl(path,data):path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data),encoding='utf-8')
    jsonl(output/'review.jsonl',valid);jsonl(output/'rejected.jsonl',rejected)
    for split,values in partitions.items():jsonl(output/(split+'.jsonl'),values)
    manifest={'schema_version':1,'fingerprint':fingerprint,'input_sha256':input_hash,'seed':SEED,'near_duplicate_algorithm':'character 5-gram Jaccard','near_duplicate_threshold':NEAR_THRESHOLD,
     'input_count':len(rows),'review_count':len(valid),'rejected_count':len(rejected),'unique_normalized_texts':len(unique),'near_duplicate_edges':near_edges,
     'synthetic_count':sum(r['source_type']=='synthetic' for r in valid),'review_status_counts':dict(Counter(r.get('review_status','NEEDS_REVIEW') for r in valid)),
     'proposed_label_counts':dict(Counter(str(r.get('proposed_label')) for r in valid)),
     'partition_counts':{k:len(v) for k,v in partitions.items()},'conflicting_verified_texts':len(conflicts),
     'training_performed':False,'ready_for_training':False,'status':'READY_FOR_REVIEW','source_manifest':source_manifest or {},
     'outputs_sha256':{p.name:digest(p) for p in output.glob('*.jsonl')}}
    (output/'dataset_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest

def local_sources():
    rows=[];sources={}
    source_paths=list((ROOT/'datasets/fixtures/genz_regression').glob('*.json'))
    source_paths+=[ROOT/'datasets/review/conversations_100/conversations_labeled.json']
    for p in source_paths:
        if not p.exists():continue
        rel=p.relative_to(ROOT).as_posix();data=json.loads(p.read_text(encoding='utf-8'))
        regression=p.parent.name=='genz_regression'
        sources[rel]={'sha256':digest(p),'source_type':'synthetic','rights_status':'project_supplied_for_local_review; external reuse not verified','model_id':None,'prompt_or_generation_notes':'source task pack / conversation generator','regression_only':regression,'used_in_prior_training':not regression}
        for t in [data] if regression else data['threads']:
            for c in t['comments']:
                rows.append({'thread_id':t['thread_id'],'comment_id':c['comment_id'],'user_id':c['user_id'],'parent_id':c.get('parent_id'),'timestamp':c['timestamp'],'raw_text':c['text'],
                 'source_id':rel,'source_type':'synthetic','split':'development_regression' if regression else 'review_pool',
                 'proposed_label':c.get('annotation',{}).get('suggested_toxicity'),'human_label':None,'review_status':'NEEDS_REVIEW',
                 'approved_for_training':False,'license_approved':False,'used_in_prior_training':not regression})
    catalog=json.loads((ROOT/'datasets/manifest.json').read_text(encoding='utf-8'))
    audit={k:{'task':v['task'],'license':v['license'],'total_rows':v['total_rows'],'loaded_for_this_import':False} for k,v in catalog['sources'].items()}
    sources['existing_dataset_catalog_only']=audit
    return rows,sources
if __name__=='__main__':
    rows,sources=local_sources();result=prepare(rows,ROOT/'datasets/ai-update/review_v1',sources)
    print(json.dumps({k:result[k] for k in ('status','input_count','review_count','unique_normalized_texts','partition_counts','training_performed')},ensure_ascii=True))
