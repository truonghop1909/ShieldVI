"""Immutable bounded imports using existing normalization/PII/leakage utilities."""
import csv,hashlib,hmac,io,json,re,secrets,sqlite3
from collections import Counter,defaultdict
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,AwareDatetime,ValidationError
from real_dataset.core import comparison,near_similarity,pii_hits,sha_file,atomic_json,now
from real_dataset.leakage import development_index
ROOT=Path(__file__).resolve().parents[2]
EXCLUSIONS=ROOT/'datasets/real_conversations/manifests/development_exclusions.research_v62_20261104.json'
MAX_BYTES=1048576;ID=r'^[A-Za-z0-9_.-]{1,120}$'
FIELDS=('text','label','thread_id','comment_id','parent_id','user_id','timestamp','target_user_id','category','severity','source')

class ImportInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    content:str=Field(min_length=1,max_length=MAX_BYTES)
    format:Literal['csv','json','jsonl']
    dataset_type:Literal['PRELABELED','UNLABELED','SYNTHETIC','HUMAN_REVIEWED']
    data_origin:Literal['synthetic','real']
    mapping:dict[str,str]=Field(default_factory=dict,max_length=11)
    provenance:dict=Field(default_factory=dict)
    parent_version:str|None=Field(default=None,pattern=r'^[0-9a-f]{24}$')

class Row(BaseModel):
    model_config=ConfigDict(extra='forbid')
    text:str=Field(min_length=1,max_length=8000)
    label:Literal['CLEAN','TOXIC','UNCERTAIN']|None=None
    thread_id:str=Field(pattern=ID)
    comment_id:str=Field(pattern=ID)
    parent_id:str|None=Field(default=None,pattern=ID)
    user_id:str=Field(pattern=ID)
    timestamp:AwareDatetime
    target_user_id:str|None=Field(default=None,pattern=ID)
    category:str|None=Field(default=None,max_length=100)
    severity:str|None=Field(default=None,max_length=40)
    source:str|None=Field(default=None,max_length=2000)

def digest(value):return hashlib.sha256(value).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def safe_csv(rows):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(rows[0]) if rows else list(FIELDS));writer.writeheader()
    for row in rows:writer.writerow({k:("'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v) for k,v in row.items()})
    return stream.getvalue()

class DatasetStore:
    def __init__(self,root,project=ROOT):
        self.root=Path(root).resolve();self.project=Path(project).resolve()
        if not (self.root/'studio.json').is_file():raise ValueError('Initialize an explicit local Studio root first')
        self.marker=json.loads((self.root/'studio.json').read_text(encoding='utf-8'))
        if self.marker.get('schema_version')!='studio-1.0':raise ValueError('Unsupported Studio version')
        self.key=bytes.fromhex((self.root/'private_key').read_text(encoding='ascii'))
        audit=self.root/'exclusion_audit/manifests/development_exclusions.json'
        if sha_file(audit)!=self.marker['exclusions_sha256']:raise ValueError('Exclusion snapshot changed')
        self.excluded_threads,self.excluded_hashes,groups=development_index(self.root/'exclusion_audit',self.project)
        self.excluded_hashes.update(digest(comparison(t).encode()) for texts in groups.values() for t in texts if len(comparison(t))>=40)
        self.group_texts=[comparison('\n'.join(texts)) for texts in groups.values()]
        self.development_texts={comparison(t) for texts in groups.values() for t in texts if len(comparison(t))>=40}
        # CSV supervised splits have no thread IDs; preserve their text for near-overlap auditing too.
        known=json.loads(audit.read_text(encoding='utf-8'))
        for ref in known.get('source_records',[]):
            if ref.get('format')=='csv':
                with (self.project/ref['path']).open(encoding='utf-8-sig',newline='') as stream:
                    self.development_texts.update(comparison(row[ref['text_field']]) for row in csv.DictReader(stream) if len(comparison(row[ref['text_field']]))>=40)
    @classmethod
    def initialize(cls,root,exclusions=EXCLUSIONS,project=ROOT):
        root=Path(root).resolve();project=Path(project).resolve()
        if not root.is_relative_to(project) or root==project:raise ValueError('Studio root must be inside the project')
        if root.exists() and any(root.iterdir()):raise ValueError('Studio requires a new empty directory')
        root.mkdir(parents=True,exist_ok=True);audit=root/'exclusion_audit/manifests/development_exclusions.json'
        atomic_json(audit,json.loads(Path(exclusions).read_text(encoding='utf-8-sig')));development_index(root/'exclusion_audit',project)
        (root/'private_key').write_text(secrets.token_hex(32),encoding='ascii')
        atomic_json(root/'studio.json',{'schema_version':'studio-1.0','exclusions_sha256':sha_file(audit),'created_at':now()})
        with sqlite3.connect(root/'studio.sqlite3') as db:
            db.executescript('''CREATE TABLE datasets(id TEXT PRIMARY KEY,request_sha TEXT NOT NULL UNIQUE,source_sha TEXT NOT NULL,status TEXT NOT NULL,created_by TEXT NOT NULL,created_at TEXT NOT NULL,report_json TEXT NOT NULL,manifest_json TEXT NOT NULL);
                CREATE TABLE studio_audit(id INTEGER PRIMARY KEY,actor_id TEXT NOT NULL,event TEXT NOT NULL,entity_id TEXT NOT NULL,created_at TEXT NOT NULL,details_json TEXT NOT NULL);
                CREATE TABLE training_runs(id TEXT PRIMARY KEY,owner_id TEXT NOT NULL,idempotency_key TEXT NOT NULL,config_json TEXT NOT NULL,preflight_json TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,heartbeat REAL,error_code TEXT,UNIQUE(owner_id,idempotency_key));''')
        return cls(root,project)
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.root/'studio.sqlite3',timeout=20);db.row_factory=sqlite3.Row
        try:yield db;db.commit()
        except BaseException:db.rollback();raise
        finally:db.close()
    def audit(self,db,actor,event,entity,details):db.execute('INSERT INTO studio_audit(actor_id,event,entity_id,created_at,details_json) VALUES(?,?,?,?,?)',(actor,event,entity,now(),json.dumps(details)))
    def list(self):
        with self.connect() as db:rows=db.execute('SELECT id,status,created_at,manifest_json FROM datasets ORDER BY created_at DESC LIMIT 200').fetchall()
        return [{'id':r['id'],'status':r['status'],'created_at':r['created_at'],'manifest':json.loads(r['manifest_json'])} for r in rows]
    def get(self,identity):
        if not re.fullmatch(r'[0-9a-f]{24}',identity):raise KeyError('Unknown dataset')
        with self.connect() as db:row=db.execute('SELECT * FROM datasets WHERE id=?',(identity,)).fetchone()
        if not row:raise KeyError('Unknown dataset')
        return {'id':identity,'status':row['status'],'report':json.loads(row['report_json']),'manifest':json.loads(row['manifest_json'])}
    def rows(self,identity):
        record=self.get(identity);path=self.root/'versions'/identity/'comments.jsonl'
        if sha_file(path)!=record['manifest']['normalized_sha256']:raise ValueError('Immutable dataset content changed')
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line]
    def parse(self,payload):
        if len(payload.content.encode('utf-8'))>MAX_BYTES:raise ValueError('Upload exceeds 1 MiB')
        if any(k not in FIELDS or not isinstance(v,str) or not v or len(v)>100 for k,v in payload.mapping.items()):raise ValueError('Unknown column mapping')
        if '\x00' in payload.content or any(0xD800<=ord(c)<=0xDFFF for c in payload.content):raise ValueError('Invalid UTF8 text')
        if payload.format=='csv':
            reader=csv.DictReader(io.StringIO(payload.content.lstrip('\ufeff')))
            if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)):raise ValueError('CSV headers missing or duplicated')
            values=list(reader)
        elif payload.format=='jsonl':values=[json.loads(line) for line in payload.content.splitlines() if line.strip()]
        else:
            data=json.loads(payload.content)
            if isinstance(data,dict) and 'comments' in data:data=[data]
            if not isinstance(data,list):raise ValueError('Expected JSON rows or threads')
            values=[]
            for item in data:
                if isinstance(item,dict) and isinstance(item.get('comments'),list):
                    for c in item['comments']:
                        if not isinstance(c,dict):raise ValueError('Comment must be an object')
                        ann=c.get('annotation') or {}
                        if not isinstance(ann,dict):raise ValueError('Annotation must be an object')
                        values.append({**c,'thread_id':item.get('thread_id'),'label':ann.get('label',c.get('label')),'target_user_id':ann.get('directed_at_user_id',c.get('target_user_id'))})
                else:values.append(item)
        if not 1<=len(values)<=1000:raise ValueError('Expected 1–1000 comments per import')
        return values
    def import_dataset(self,payload,actor,*,trusted_pseudonyms=False):
        payload=ImportInput.model_validate(payload)
        if payload.parent_version:self.get(payload.parent_version)
        request_sha=digest(canonical(payload.model_dump()));identity=request_sha[:24]
        with self.connect() as db:old=db.execute('SELECT id FROM datasets WHERE request_sha=?',(request_sha,)).fetchone()
        if old:return {**self.get(old['id']),'replayed':True}
        source_sha=digest(payload.content.encode())
        with self.connect() as db:prior_sources=db.execute('SELECT id FROM datasets WHERE source_sha=?',(source_sha,)).fetchall()
        if prior_sources and payload.parent_version not in {r['id'] for r in prior_sources}:raise ValueError('Source already imported: use its explicit parent_version for changed metadata')
        errors=[];warnings=[];quarantine=[];rows=[];seen=set();groups=defaultdict(list);text_hashes={};near_cache=[]
        try:values=self.parse(payload)
        except (ValueError,TypeError,RecursionError,csv.Error) as error:values=[];errors.append({'row':0,'code':'MALFORMED_INPUT','detail':str(error)[:180]})
        for number,raw in enumerate(values,1):
            if not isinstance(raw,dict):errors.append({'row':number,'code':'ROW_NOT_OBJECT'});continue
            if None in raw:errors.append({'row':number,'code':'CSV_EXTRA_COLUMNS'});continue
            if any(source not in raw for source in payload.mapping.values()):errors.append({'row':number,'code':'MISSING_MAPPED_COLUMN'});continue
            mapped={field:raw.get(payload.mapping.get(field,field)) for field in FIELDS};mapped={k:(None if v=='' else v) for k,v in mapped.items()}
            if isinstance(mapped['label'],bool):errors.append({'row':number,'code':'INVALID_LABEL_TYPE'});continue
            if mapped['label'] in ('0',0):mapped['label']='CLEAN'
            elif mapped['label'] in ('1',1):mapped['label']='TOXIC'
            try:row=Row.model_validate(mapped).model_dump(mode='json')
            except ValidationError as error:errors.append({'row':number,'code':'INVALID_SCHEMA','fields':[str(e['loc'][0]) for e in error.errors()]});continue
            key=(row['thread_id'],row['comment_id'])
            if key in seen:errors.append({'row':number,'code':'DUPLICATE_COMMENT_ID'});continue
            seen.add(key)
            if not row['text'].strip():errors.append({'row':number,'code':'EMPTY_TEXT'})
            if any(isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) for k,v in row.items() if k!='timestamp'):quarantine.append({'row':number,'code':'CSV_FORMULA_RISK'})
            pii=pii_hits(row['text'])
            if pii:quarantine.append({'row':number,'code':'PII_REQUIRES_REDACTION','types':sorted({p[2] for p in pii})})
            text=comparison(row['text']);sha=digest(text.encode())
            if sha in text_hashes:warnings.append({'row':number,'code':'EXACT_DUPLICATE','other_row':text_hashes[sha]})
            else:text_hashes[sha]=number
            if row['thread_id'] in self.excluded_threads or (len(text)>=40 and sha in self.excluded_hashes):quarantine.append({'row':number,'code':'DEVELOPMENT_OR_PRIOR_SPLIT_OVERLAP'})
            for old_number,old_text in near_cache:
                if len(text)>=40 and abs(len(old_text)-len(text))<=max(len(old_text),len(text))*.15 and near_similarity(text,old_text)>=.9:
                    warnings.append({'row':number,'code':'NEAR_DUPLICATE','other_row':old_number});break
            near_cache.append((number,text));groups[row['thread_id']].append(row);rows.append(row)
        for tid,items in groups.items():
            users={r['user_id'] for r in items};ids={r['comment_id']:r for r in items};prior=set();last=None
            for row in items:
                stamp=datetime.fromisoformat(row['timestamp'].replace('Z','+00:00'));parent=row['parent_id']
                if parent and (parent not in prior or datetime.fromisoformat(ids[parent]['timestamp'].replace('Z','+00:00'))>stamp):errors.append({'thread_id':tid,'comment_id':row['comment_id'],'code':'PARENT_MISSING_FUTURE_OR_CYCLE'})
                if last and stamp<last:errors.append({'thread_id':tid,'code':'TIMESTAMP_ORDER'})
                if row['target_user_id'] and (row['target_user_id'] not in users or row['target_user_id']==row['user_id']):errors.append({'thread_id':tid,'code':'INVALID_TARGET'})
                prior.add(row['comment_id']);last=stamp
            text=comparison('\n'.join(r['text'] for r in items))
            if any(len(text)>=80 and abs(len(old)-len(text))<=max(len(old),len(text))*.15 and near_similarity(text,old)>=.9 for old in self.group_texts):quarantine.append({'thread_id':tid,'code':'NEAR_DEVELOPMENT_THREAD_OVERLAP'})
        comparisons=0;budget_reached=False
        for row in rows:
            text=comparison(row['text'])
            if len(text)<40:continue
            for old in self.development_texts:
                if abs(len(old)-len(text))>max(len(old),len(text))*.15:continue
                comparisons+=1
                if comparisons>1000000:budget_reached=True;break
                if near_similarity(text,old)>=.9:quarantine.append({'thread_id':row['thread_id'],'comment_id':row['comment_id'],'code':'NEAR_DEVELOPMENT_COMMENT_OVERLAP'});break
            if budget_reached:break
        if budget_reached:quarantine.append({'code':'NEAR_DUPLICATE_AUDIT_BUDGET_REACHED','action':'split the upload into smaller versions; unverified data cannot train'})
        if payload.data_origin=='real':quarantine.append({'code':'REAL_SOURCE_RIGHTS_REQUIRE_MANUAL_VERIFICATION','missing':[k for k in ('source_url','license','license_url','consent_basis','permitted_use','receipt') if not payload.provenance.get(k)]})
        if payload.dataset_type=='HUMAN_REVIEWED':quarantine.append({'code':'HUMAN_CLAIM_REQUIRES_REVIEW_HISTORY'})
        if payload.dataset_type=='UNLABELED' and any(r['label'] for r in rows):errors.append({'code':'UNLABELED_CONTAINS_LABELS'})
        if payload.dataset_type in ('PRELABELED','SYNTHETIC') and any(r['label'] is None for r in rows):errors.append({'code':'MISSING_REFERENCE_LABEL'})
        status='REJECTED' if errors else 'QUARANTINED' if quarantine else 'ACCEPTED'
        for old in self.list():
            if old['status']!='ACCEPTED' or old['id']==payload.parent_version:continue
            if any(digest(comparison(r['text']).encode()) in text_hashes for r in self.rows(old['id'])):warnings.append({'code':'PREVIOUS_STUDIO_DATASET_OVERLAP','dataset_id':old['id']})
        trusted_users={r['user_id'] for r in self.rows(payload.parent_version)} if trusted_pseudonyms and payload.parent_version else set()
        if trusted_pseudonyms and not payload.parent_version:raise ValueError('Trusted export requires parent lineage')
        def pseudo(value):
            if trusted_pseudonyms and value:
                if value not in trusted_users:raise ValueError('Unknown trusted participant')
                return value
            return 'U_'+hmac.new(self.key,value.encode(),hashlib.sha256).hexdigest()[:16] if value else None
        for row in rows:
            row['user_id']=pseudo(row['user_id']);row['target_user_id']=pseudo(row['target_user_id']);row['data_origin']=payload.data_origin
            row['label_source']='synthetic_reference' if payload.data_origin=='synthetic' and row['label'] else 'unverified_source' if row['label'] else None
            bucket=int(digest(row['thread_id'].encode())[:8],16)%100;row['split']='train' if bucket<70 else 'validation' if bucket<85 else 'test'
        normalized=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows).encode()
        report={'schema_version':'studio-quality-1.0','errors':errors,'quarantine':quarantine,'warnings':warnings,'comments':len(rows),'threads':len(groups),'labels':dict(Counter(r['label'] or 'UNLABELED' for r in rows)),
            'review_ratio':0,'near_comparisons':comparisons,'near_duplicate_policy':'Normalized comment >=40 chars and development whole-thread Jaccard >=0.90; 1M comparison cap fails closed; unknown pretraining not auditable',
            'training_eligible':status=='ACCEPTED' and payload.data_origin=='synthetic' and all(r['label'] in ('CLEAN','TOXIC') for r in rows) and not warnings}
        source_sha=digest(payload.content.encode());manifest={'schema_version':'studio-dataset-1.0','data_origin':payload.data_origin,'dataset_type':payload.dataset_type,'source_sha256':source_sha,'normalized_sha256':digest(normalized),'request_sha256':request_sha,
            'parent_version':payload.parent_version,'provenance':payload.provenance,'exclusions_sha256':self.marker['exclusions_sha256'],'split_policy':'thread-sha256-70-15-15-v1','split_locked':True,
            'label_source':'synthetic_reference' if payload.data_origin=='synthetic' else 'unverified_source','counts':{k:sum(r['split']==k for r in rows) for k in ('train','validation','test')},'comments':len(rows),'threads':len(groups),'not_human_gold':True}
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE');old=db.execute('SELECT id FROM datasets WHERE request_sha=?',(request_sha,)).fetchone()
            if old:return {**self.get(old['id']),'replayed':True}
            target=self.root/'versions'/identity;target.mkdir(parents=True,exist_ok=True)
            for name,content in [('source.txt',payload.content.encode()),('comments.jsonl',normalized)]:
                path=target/name
                if path.exists() and path.read_bytes()!=content:raise ValueError('Immutable artifact collision')
                if not path.exists():
                    with path.open('xb') as output:output.write(content)
            atomic_json(target/'manifest.json',manifest);atomic_json(target/'quality_report.json',report)
            db.execute('INSERT INTO datasets VALUES(?,?,?,?,?,?,?,?)',(identity,request_sha,source_sha,status,actor,now(),json.dumps(report),json.dumps(manifest)));self.audit(db,actor,'DATASET_IMPORTED',identity,{'status':status,'source_sha256':source_sha})
        return {**self.get(identity),'replayed':False}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--initialize',required=True);args=parser.parse_args();value=DatasetStore.initialize(args.initialize);print(json.dumps({'root':str(value.root),'initialized':True}))
