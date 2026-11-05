"""Solo annotation adapter; existing ReviewStore owns CAS, history and evidence checks."""
import json
from collections import defaultdict
from datetime import datetime,timezone
from pydantic import ConfigDict,Field
from typing import Literal
from real_dataset.store import ReviewStore,AnnotationInput,RevisionConflict
from real_dataset.core import atomic_json,now
from .datasets import ImportInput,canonical,digest

class StudioAnnotation(AnnotationInput):
    model_config=ConfigDict(extra='forbid')
    severity:Literal['none','low','medium','high']|None=None
    is_intervention:bool|None=None
    is_defense:bool|None=None
    is_profanity_non_directed:bool|None=None

class StudioReviews(ReviewStore):
    annotation_model=StudioAnnotation
    def __init__(self,datasets,identity):
        self.datasets=datasets;self.identity=identity;record=datasets.get(identity)
        if record['status']!='ACCEPTED':raise ValueError('Only ACCEPTED dataset versions can be annotated')
        self.origin=record['manifest']['data_origin'];super().__init__(datasets.root/'annotation_sessions'/identity)
    def corpus(self):
        groups=defaultdict(list)
        for r in self.datasets.rows(self.identity):groups[r['thread_id']].append({k:r[k] for k in ('comment_id','parent_id','user_id','timestamp','text')})
        return {tid:{'thread_id':tid,'comments':rows,'data_origin':self.origin} for tid,rows in groups.items()}
    def validate(self,a,db,corpus):
        super().validate(a,db,corpus)
        if a.review_round==2 and self.origin=='real':
            first=self._existing(db,(a.thread_id,a.comment_id,a.reviewer_id,1));elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(first['updated_at'])).total_seconds()
            if elapsed<300:raise ValueError('Real-data Round 2 requires at least 300 seconds after the last Round 1 update')
    def visible(self,reviewer):
        rows=super().list_reviews(reviewer_id=reviewer);first={(r['thread_id'],r['comment_id']):r for r in rows if r['review_round']==1}
        result=[]
        for row in rows:
            r1=first.get((row['thread_id'],row['comment_id']));valid=row['review_round']==1 or bool(r1 and r1['annotation_status']=='ROUND1_DONE' and row['round1_revision']==r1['revision'])
            state='DISPUTED' if row['label']=='UNCERTAIN' else 'REVIEWED' if row['annotation_status']=='ROUND2_DONE' and valid else 'SUBMITTED' if row['annotation_status']=='ROUND1_DONE' else 'DRAFT'
            result.append({**row,'round2_valid':valid,'review_state':state})
        return result
    def update_progress(self):
        rows=super().list_reviews();reviewers={r['reviewer_id'] for r in rows};valid=[r for actor in reviewers for r in self.visible(actor) if r['review_round']==2 and r['round2_valid'] and r['annotation_status']=='ROUND2_DONE']
        atomic_json(self.root/'manifests/progress.json',{'total_comments':sum(len(t['comments']) for t in self.corpus().values()),'valid_round2':len(valid),'reviewers':len(reviewers),'not_inter_annotator_agreement':True,'updated_at':now()})
    def snapshot(self,reviewer):
        reviews=self.visible(reviewer);complete={(r['thread_id'],r['comment_id']):r for r in reviews if r['review_round']==2 and r['round2_valid'] and r['annotation_status']=='ROUND2_DONE'}
        source=self.datasets.rows(self.identity)
        if any((r['thread_id'],r['comment_id']) not in complete for r in source):raise ValueError('Complete valid Round 2 for every comment before export; changed Round 1 invalidates previous confirmation')
        # The receipt is provenance, not proof of two independent reviewers or human gold.
        receipt={'dataset_version':self.identity,'reviewer_id':reviewer,'reviews':list(complete.values()),'data_origin':self.origin,'human_gold':False,'same_reviewer_two_rounds':True}
        sha=digest(canonical(receipt));path=self.root/'snapshots'/sha
        if not path.exists():path.mkdir(parents=True);atomic_json(path/'reviews.json',receipt)
        rows=[]
        for r in source:
            ann=complete[(r['thread_id'],r['comment_id'])]
            rows.append({**r,'label':ann['label'],'target_user_id':ann['directed_at_user_id'],'category':ann['category'],'severity':ann['severity']})
        payload=ImportInput(content=json.dumps(rows,ensure_ascii=False),format='json',dataset_type='PRELABELED',data_origin=self.origin,parent_version=self.identity,
            provenance={'annotation_receipt_sha256':sha,'solo_review':True,'human_gold':False,'synthetic_reference_remains_synthetic':self.origin=='synthetic'})
        result=self.datasets.import_dataset(payload,reviewer,trusted_pseudonyms=True)
        with self.datasets.connect() as db:self.datasets.audit(db,reviewer,'ANNOTATION_SNAPSHOT_LOCKED',result['id'],{'receipt_sha256':sha,'parent':self.identity})
        return {**result,'annotation_receipt_sha256':sha,'snapshot_state':'LOCKED','human_gold':False}
