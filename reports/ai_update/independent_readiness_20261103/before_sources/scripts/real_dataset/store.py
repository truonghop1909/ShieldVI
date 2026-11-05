from __future__ import annotations
import csv,io,json,sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Literal
from pydantic import BaseModel,Field
from .core import DATA,RealThread,load_json,now,sha_file,atomic_json,comparison,near_similarity,thread_text
class RevisionConflict(ValueError):pass
class AnnotationInput(BaseModel):
    thread_id:str
    comment_id:str
    reviewer_id:str=Field(pattern=r'^[A-Za-z0-9_-]{1,40}$')
    review_round:Literal[1,2]=1
    expected_revision:int=Field(ge=0)
    round1_revision:int|None=None
    label:Literal['CLEAN','TOXIC','UNCERTAIN']|None=None
    category:Literal['normal','profanity','directed_insult','indirect_attack','defense','intervention','quote','apology','reconciliation','other']|None=None
    directed_at_user_id:str|None=None
    is_directed_attack:bool|None=None
    is_repeated_attack:bool|None=None
    is_apology:bool|None=None
    is_quote:bool|None=None
    confidence:Literal['low','medium','high']|None=None
    reviewer_notes:str=Field(default='',max_length=5000)
    evidence_comment_ids:list[str]=Field(default_factory=list,max_length=100)
    annotation_status:Literal['DRAFT','ROUND1_DONE','ROUND2_DONE']='DRAFT'
    change_reason:str=Field(default='',max_length=1000)
class ReviewStore:
    annotation_model=AnnotationInput
    def __init__(self,data_root=DATA):
        self.root=Path(data_root);self.path=self.root/'annotations/reviews.sqlite3';self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS reviews(
                thread_id TEXT NOT NULL,comment_id TEXT NOT NULL,reviewer_id TEXT NOT NULL,review_round INTEGER NOT NULL,
                revision INTEGER NOT NULL,label TEXT,annotation_status TEXT NOT NULL,payload_json TEXT NOT NULL,updated_at TEXT NOT NULL,
                PRIMARY KEY(thread_id,comment_id,reviewer_id,review_round));
                CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY,thread_id TEXT NOT NULL,comment_id TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,review_round INTEGER NOT NULL,previous_label TEXT,new_label TEXT,review_timestamp TEXT NOT NULL,
                change_reason TEXT NOT NULL,previous_json TEXT,new_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS thread_checks(thread_id TEXT NOT NULL,reviewer_id TEXT NOT NULL,source_reviewed INTEGER NOT NULL,
                privacy_reviewed INTEGER NOT NULL,completeness_reviewed INTEGER NOT NULL,dataset_sha256 TEXT NOT NULL,reviewed_at TEXT NOT NULL,
                PRIMARY KEY(thread_id,reviewer_id));''')
    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=20);db.row_factory=sqlite3.Row;db.execute('PRAGMA busy_timeout=20000')
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:db.close()
    def corpus(self):return {t['thread_id']:t for t in [RealThread.model_validate(load_json(p)).model_dump(mode='json') for p in (self.root/'threads').glob('*.json')]}
    def _existing(self,db,key):
        row=db.execute('SELECT * FROM reviews WHERE thread_id=? AND comment_id=? AND reviewer_id=? AND review_round=?',key).fetchone()
        return dict(row) if row else None
    def validate(self,a,db,corpus):
        t=corpus.get(a.thread_id)
        if not t:raise ValueError('Unknown thread')
        comments={c['comment_id']:c for c in t['comments']};c=comments.get(a.comment_id)
        if not c:raise ValueError('Unknown comment')
        users={x['user_id'] for x in comments.values() if x['user_id']}
        if a.directed_at_user_id and (a.directed_at_user_id not in users or a.directed_at_user_id==c['user_id']):raise ValueError('Target must be another known participant')
        if a.label=='UNCERTAIN' and not a.reviewer_notes.strip():raise ValueError('UNCERTAIN requires reviewer notes')
        if a.annotation_status!='DRAFT' and a.label is None:raise ValueError('A completed review requires an explicit label')
        if a.annotation_status=='ROUND1_DONE' and a.review_round!=1 or a.annotation_status=='ROUND2_DONE' and a.review_round!=2:raise ValueError('Review status/round mismatch')
        if a.review_round==2:
            first=self._existing(db,(a.thread_id,a.comment_id,a.reviewer_id,1))
            if not first or first['annotation_status']!='ROUND1_DONE':raise ValueError('Complete your own Round 1 before Round 2')
            if a.round1_revision!=first['revision']:raise RevisionConflict('Round 1 changed: reload and explicitly confirm Round 2 again')
        if a.is_repeated_attack:
            if not c.get('timestamp') or not c.get('user_id'):raise ValueError('Repeated evidence requires known source actor and timestamp')
            if not a.is_directed_attack or not a.directed_at_user_id:raise ValueError('Repeated attack requires explicit directed attack and known target')
            evidence=list(dict.fromkeys(a.evidence_comment_ids))
            if len(evidence)<2 or a.comment_id not in evidence:raise ValueError('Repeated evidence must include this comment and at least one other distinct turn')
            stamps=set()
            for cid in evidence:
                row=comments.get(cid)
                if not row or row['user_id']!=c['user_id'] or not row.get('timestamp'):raise ValueError('Evidence must have same actor and source timestamps')
                from datetime import datetime
                stamp=datetime.fromisoformat(row['timestamp'].replace('Z','+00:00'));current=datetime.fromisoformat(c['timestamp'].replace('Z','+00:00'))
                if stamp>current:raise ValueError('Future turns cannot prove repeated attack at this turn')
                stamps.add(stamp)
                if cid!=a.comment_id:
                    existing=db.execute('SELECT payload_json FROM reviews WHERE thread_id=? AND comment_id=? AND reviewer_id=? AND review_round<=? ORDER BY review_round DESC LIMIT 1',(a.thread_id,cid,a.reviewer_id,a.review_round)).fetchone()
                    prior=json.loads(existing['payload_json']) if existing else {}
                    if not prior.get('is_directed_attack') or prior.get('directed_at_user_id')!=a.directed_at_user_id:raise ValueError('Earlier evidence must already be human-labeled directed at the same target')
            if len(stamps)<2:raise ValueError('Repeated evidence requires distinct source timestamps')
    def _save(self,db,a,corpus):
        self.validate(a,db,corpus)
        key=(a.thread_id,a.comment_id,a.reviewer_id,a.review_round);existing=self._existing(db,key)
        revision=existing['revision'] if existing else 0
        if revision!=a.expected_revision:raise RevisionConflict('Stale revision: reload before changing this annotation')
        old_payload=json.loads(existing['payload_json']) if existing else None
        previous_label=existing['label'] if existing else None
        if not existing and a.review_round==2:
            previous=self._existing(db,(a.thread_id,a.comment_id,a.reviewer_id,1));previous_label=previous['label']
        if previous_label is not None and previous_label!=a.label and not a.change_reason.strip():raise ValueError('Label changes require a change reason')
        value=a.model_dump(exclude={'expected_revision','change_reason'})
        if old_payload==value:return {**value,'revision':revision,'updated_at':existing['updated_at']}
        revision+=1;stamp=now();raw=json.dumps(value,ensure_ascii=False)
        db.execute('''INSERT INTO reviews VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(thread_id,comment_id,reviewer_id,review_round)
          DO UPDATE SET revision=excluded.revision,label=excluded.label,annotation_status=excluded.annotation_status,payload_json=excluded.payload_json,updated_at=excluded.updated_at''',
          (*key,revision,a.label,a.annotation_status,raw,stamp))
        reason=a.change_reason or ('initial_human_entry' if previous_label is None else 'human_confirmation_or_metadata_edit')
        db.execute('INSERT INTO history(thread_id,comment_id,reviewer_id,review_round,previous_label,new_label,review_timestamp,change_reason,previous_json,new_json) VALUES(?,?,?,?,?,?,?,?,?,?)',
          (*key,previous_label,a.label,stamp,reason,existing['payload_json'] if existing else None,raw))
        return {**value,'revision':revision,'updated_at':stamp}
    def assert_unlocked(self):
        if (self.root/'manifests/evaluation_lock.json').exists():raise RevisionConflict('Evaluation locked: create a new version before editing')
    def save(self,payload):
        self.assert_unlocked()
        a=self.annotation_model.model_validate(payload);corpus=self.corpus()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE');result=self._save(db,a,corpus)
        self.update_progress();return result
    def list_reviews(self,thread_id=None,reviewer_id=None,review_round=None):
        where=[];params=[]
        for name,value in [('thread_id',thread_id),('reviewer_id',reviewer_id),('review_round',review_round)]:
            if value is not None:where.append(name+'=?');params.append(value)
        with self.connect() as db:
            rows=db.execute('SELECT * FROM reviews'+(' WHERE '+' AND '.join(where) if where else '')+' ORDER BY thread_id,comment_id,reviewer_id,review_round',params).fetchall()
        return [{**json.loads(r['payload_json']),'revision':r['revision'],'updated_at':r['updated_at']} for r in rows]
    def history(self,thread_id,comment_id):
        with self.connect() as db:return [dict(r) for r in db.execute('SELECT reviewer_id,review_round,previous_label,new_label,review_timestamp,change_reason FROM history WHERE thread_id=? AND comment_id=? ORDER BY id',(thread_id,comment_id))]
    def check_thread(self,thread_id,reviewer_id,source_reviewed,privacy_reviewed,completeness_reviewed):
        self.assert_unlocked()
        if thread_id not in self.corpus() or not reviewer_id:raise ValueError('Thread and reviewer required')
        path=self.root/'threads'/(thread_id+'.json')
        with self.connect() as db:db.execute('INSERT INTO thread_checks VALUES(?,?,?,?,?,?,?) ON CONFLICT(thread_id,reviewer_id) DO UPDATE SET source_reviewed=excluded.source_reviewed,privacy_reviewed=excluded.privacy_reviewed,completeness_reviewed=excluded.completeness_reviewed,dataset_sha256=excluded.dataset_sha256,reviewed_at=excluded.reviewed_at',
          (thread_id,reviewer_id,int(source_reviewed),int(privacy_reviewed),int(completeness_reviewed),sha_file(path),now()))
    def update_progress(self):
        progress=load_json(self.root/'manifests/progress.json',{})
        latest={}
        for row in self.list_reviews():
            key=(row['thread_id'],row['comment_id'])
            if key not in latest or row['updated_at']>latest[key]['updated_at']:latest[key]=row
        progress.update(annotated_comments=sum(r['label'] is not None for r in latest.values()),
          unlabeled_comments=max(0,sum(len(t['comments']) for t in self.corpus().values())-sum(r['label'] is not None for r in latest.values())),
          uncertain_comments=sum(r['label']=='UNCERTAIN' for r in latest.values()),
          round2_done=sum(r['annotation_status']=='ROUND2_DONE' for r in latest.values()),
          annotation_updated_at=now())
        atomic_json(self.root/'manifests/progress.json',progress)
    def quality_errors(self):
        corpus=self.corpus();errors=[]
        with self.connect() as db:
            for raw in self.list_reviews():
                try:self.validate(self.annotation_model.model_validate({**{k:v for k,v in raw.items() if k not in ('revision','updated_at')},'expected_revision':raw['revision']}),db,corpus)
                except ValueError:errors.append({'thread_id':raw['thread_id'],'comment_id':raw['comment_id'],'code':'invalid_saved_annotation'})
        return errors
    def export_csv(self,reviewer_id=None):
        rows=self.list_reviews(reviewer_id=reviewer_id);stream=io.StringIO(newline='')
        fields=list(self.annotation_model.model_fields)+['updated_at','_escaped_columns']
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for raw in rows:
            row={k:raw.get(k,'') for k in fields};row['expected_revision']=raw['revision'];row['change_reason']='';escaped=[]
            for name in ('reviewer_notes','change_reason'):
                val=str(row[name] or '')
                if val.lstrip().startswith(('=','+','-','@')):val="'"+val;escaped.append(name)
                row[name]=val
            row['evidence_comment_ids']=json.dumps(raw.get('evidence_comment_ids',[]));row['_escaped_columns']=json.dumps(escaped)
            for name in ('is_directed_attack','is_repeated_attack','is_apology','is_quote'):
                row[name]='' if raw.get(name) is None else 'true' if raw[name] else 'false'
            writer.writerow({k:('' if v is None else v) for k,v in row.items()})
        return '\ufeff'+stream.getvalue()
    def import_csv(self,text):
        self.assert_unlocked()
        records=[]
        for row in csv.DictReader(io.StringIO(text.lstrip('\ufeff'))):
            escaped=json.loads(row.pop('_escaped_columns','[]') or '[]');row.pop('updated_at',None)
            for key in escaped:
                if key not in ('reviewer_notes','change_reason'):raise ValueError('Invalid CSV escape metadata')
                if row.get(key,'').startswith("'"):row[key]=row[key][1:]
            row['evidence_comment_ids']=json.loads(row.get('evidence_comment_ids') or '[]')
            row['review_round']=int(row['review_round'])
            row['round1_revision']=int(row['round1_revision']) if row.get('round1_revision') else None
            for key in ('is_directed_attack','is_repeated_attack','is_apology','is_quote'):
                if row.get(key) not in ('','true','false'):raise ValueError('Invalid CSV boolean')
                row[key]=None if row[key]=='' else row[key]=='true'
            for key in ('label','category','confidence','directed_at_user_id'):row[key]=row.get(key) or None
            records.append(self.annotation_model.model_validate(row))
        keys=[(r.thread_id,r.comment_id,r.reviewer_id,r.review_round) for r in records]
        if len(keys)!=len(set(keys)):raise ValueError('Duplicate annotation keys in CSV')
        corpus=self.corpus();order={(t['thread_id'],c['comment_id']):i for t in corpus.values() for i,c in enumerate(t['comments'])}
        from datetime import datetime
        timestamps={(t['thread_id'],c['comment_id']):datetime.fromisoformat(c['timestamp'].replace('Z','+00:00')).timestamp() if c.get('timestamp') else float('inf') for t in corpus.values() for c in t['comments']}
        records.sort(key=lambda r:(r.review_round,r.thread_id,timestamps.get((r.thread_id,r.comment_id),float('inf')),order.get((r.thread_id,r.comment_id),0)))
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for r in records:self._save(db,r,corpus)
        self.update_progress();return len(records)
    def round2_queue(self,reviewer_id):
        completed={(r['thread_id'],r['comment_id']) for r in self.list_reviews(reviewer_id=reviewer_id,review_round=2) if r['annotation_status']=='ROUND2_DONE'}
        return [r for r in self.list_reviews(reviewer_id=reviewer_id,review_round=1) if r['annotation_status']=='ROUND1_DONE' and (r['thread_id'],r['comment_id']) not in completed]
    def lock_evaluation(self,reviewer_id):
        from .validation import validate_dataset
        report=validate_dataset(self.root);corpus=self.corpus()
        if not corpus or report['errors']:raise ValueError('Dataset is empty or validation failed')
        labels={(r['thread_id'],r['comment_id']):r for r in self.list_reviews(reviewer_id=reviewer_id,review_round=2) if r['annotation_status']=='ROUND2_DONE'}
        total=sum(len(t['comments']) for t in corpus.values())
        if len(labels)!=total:raise ValueError('Round 2 must be completed manually for every comment')
        with self.connect() as db:
            checks={r['thread_id']:dict(r) for r in db.execute('SELECT * FROM thread_checks WHERE reviewer_id=?',(reviewer_id,))}
        receipts={sha_file(p) for p in (self.root/'raw/cache').glob('*.json')}
        for t in corpus.values():
            if t['source_response_sha256'] not in receipts:raise ValueError('Source API receipt missing or changed')
            c=checks.get(t['thread_id'])
            if not c or not all(c[k] for k in ('source_reviewed','privacy_reviewed','completeness_reviewed')):raise ValueError('Manual source/privacy/completeness review missing')
            if c['dataset_sha256']!=sha_file(self.root/'threads'/(t['thread_id']+'.json')):raise ValueError('Dataset changed since manual review')
        # Independent-set lock refuses development/train text overlap; no model is run here.
        known=load_json(self.root/'manifests/development_exclusions.json',{})
        blocked_threads=set(known.get('thread_ids',[]));blocked_texts=set(known.get('long_text_sha256',[]))
        if not known.get('audit_completed'):raise ValueError('Development/train leakage audit missing')
        development_groups={}
        for ref in known.get('source_records',[]):
            path=(Path(__file__).resolve().parents[2]/ref['path']).resolve()
            if not path.is_relative_to(Path(__file__).resolve().parents[2]) or not path.exists() or sha_file(path)!=ref['sha256']:raise ValueError('Development exclusion source missing/changed')
            if ref.get('format')=='csv':
                from .core import sha_bytes
                with path.open(encoding='utf-8-sig',newline='') as stream:
                    for row in csv.DictReader(stream):
                        text=comparison(row[ref['text_field']])
                        if len(text)>=80:blocked_texts.add(sha_bytes(text.encode()))
            else:
                for line in path.read_text(encoding='utf-8').splitlines():
                    row=json.loads(line);development_groups.setdefault(row['thread_id'],[]).append(row.get('raw_text',''))
        for t in corpus.values():
            if any(near_similarity(thread_text(t),'\n'.join(parts))>=.9 for parts in development_groups.values()):raise ValueError('Near-duplicate development thread overlap')
            if t['thread_id'] in blocked_threads:raise ValueError('Development thread overlap')
            for c in t['comments']:
                from .core import sha_bytes
                if len(comparison(c['text']))>=80 and sha_bytes(comparison(c['text']).encode()) in blocked_texts:raise ValueError('Development text overlap')
        lock={'locked_at':now(),'reviewer_id':reviewer_id,'review_protocol':'same human two rounds; not inter-annotator agreement','threads':len(corpus),'comments':total,
          'thread_checksums':{k:sha_file(self.root/'threads'/(k+'.json')) for k in corpus},'annotations_sha256':sha_file(self.path),'source':'human_round2','training_allowed':False}
        path=self.root/'manifests/evaluation_lock.json'
        if path.exists():raise ValueError('Evaluation already locked; never overwrite a locked snapshot')
        export=[]
        for t in corpus.values():
            for c in t['comments']:
                r=labels[(t['thread_id'],c['comment_id'])]
                export.append({'thread_id':t['thread_id'],'comment_id':c['comment_id'],'user_id':c['user_id'],'parent_id':c['parent_id'],'timestamp':c['timestamp'],
                  'raw_text':c['text'],'text_origin':'source visible text after recorded privacy redactions','source_type':'real_anonymized','source_url':t['source_url'],'source_license':t['source_license'],
                  'rights_status':'approved','rights_reference':t['attribution_url'],'split':'blind_evaluation','used_for_training':False,'used_for_rule_development':False,
                  'comment_label':r['label'],'review_status':'VERIFIED_SOLO','annotator_id':reviewer_id,'reviewed_at':r['updated_at'],'review_round':2,
                  'context_annotation':{k:r.get(k) for k in ('category','directed_at_user_id','is_directed_attack','is_repeated_attack','is_apology','is_quote','confidence','reviewer_notes','evidence_comment_ids')}})
        export_path=self.root/'annotations/evaluation_export.jsonl'
        if export_path.exists():raise ValueError('Evaluation export exists; do not overwrite')
        export_path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in export),encoding='utf-8')
        lock.update(evaluation_eligible=True,export_file=str(export_path),export_sha256=sha_file(export_path))
        atomic_json(path,lock)
        self.update_progress()
        progress=load_json(self.root/'manifests/progress.json',{});progress['evaluation_locked']=True;atomic_json(self.root/'manifests/progress.json',progress)
        return lock
