"""Human overlay for synthetic candidates. Never changes source JSON/CSV or T028."""
from __future__ import annotations
import copy,json,re
from pathlib import Path
from typing import Literal
from pydantic import Field
from real_dataset.store import AnnotationInput,ReviewStore,RevisionConflict
from real_dataset.core import atomic_json,load_json,sha_file,now
from .pipeline import DATA,Thread

CATEGORIES=[('normal','Trao đổi bình thường'),('criticism','Phê bình hợp lý'),('profanity_exclamation','Cảm thán tục'),
 ('directed_insult','Xúc phạm trực tiếp'),('indirect_attack','Công kích gián tiếp'),('defense','Tự vệ'),
 ('intervention','Can ngăn'),('quote','Trích dẫn phản đối'),('apology','Xin lỗi'),('reconciliation','Hòa giải'),
 ('mixed_apology_attack','Xin lỗi kèm công kích'),('endorsed_quote','Trích dẫn để công kích'),('ambiguous','Mơ hồ'),('other','Khác')]
FIELDS=('label','category','directed_at_user_id','is_directed_attack','is_repeated_attack','is_apology','is_quote','evidence_comment_ids')
DONE={'ROUND1_DONE','ROUND2_DONE'}

class SyntheticAnnotation(AnnotationInput):
    category:Literal['normal','criticism','profanity_exclamation','directed_insult','indirect_attack','defense','intervention','quote','apology','reconciliation','mixed_apology_attack','endorsed_quote','ambiguous','other']|None=None
    source_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')

class SyntheticReviewStore(ReviewStore):
    annotation_model=SyntheticAnnotation
    def __init__(self,data_root=DATA):
        self.dataset_root=Path(data_root)
        self._cache_key=None;self._cache={}
        super().__init__(self.dataset_root/'human_review')

    def corpus(self):
        manifest_path=self.dataset_root/'manifest.json'
        files=sorted((self.dataset_root/'threads').glob('*.json'))
        key=(sha_file(manifest_path),tuple((p.name,p.stat().st_mtime_ns,p.stat().st_size) for p in files))
        if key!=self._cache_key:
            manifest=load_json(manifest_path);checksums=manifest.get('thread_checksums',{})
            result={}
            for path in files:
                checksum=sha_file(path);t=Thread.model_validate(load_json(path)).model_dump(mode='json')
                if path.name!=t['thread_id']+'.json' or checksums.get(t['thread_id'])!=checksum:
                    raise RevisionConflict('Nguồn synthetic khác checksum manifest; giữ dữ liệu duyệt và kiểm tra phiên bản nguồn trước.')
                t.update(source_sha256=checksum,source_platform='synthetic',source_url=None,display_title=t['title'])
                result[t['thread_id']]=t
            if set(result)!=set(checksums) or len(result)!=manifest.get('actual_threads'):
                raise RevisionConflict('Danh sách thread khác manifest synthetic; không duyệt nhầm phiên bản.')
            self._cache=result;self._cache_key=key
        return copy.deepcopy(self._cache)

    def validate(self,a,db,corpus):
        t=corpus.get(a.thread_id)
        if not t or a.source_sha256!=t['source_sha256']:
            raise RevisionConflict('Nguồn đã thay đổi; tải lại trước khi duyệt.')
        comment=next((c for c in t['comments'] if c['comment_id']==a.comment_id),None)
        if not comment:raise ValueError('Unknown comment')
        existing=self._existing(db,(a.thread_id,a.comment_id,a.reviewer_id,a.review_round))
        if existing:
            old=json.loads(existing['payload_json'])
            if old.get('source_sha256')!=a.source_sha256:
                raise RevisionConflict('Nhãn lưu thuộc bản nguồn khác; giữ bản cũ và dùng phiên bản review mới.')
        elif a.review_round==2:
            first=self._existing(db,(a.thread_id,a.comment_id,a.reviewer_id,1))
            old=json.loads(first['payload_json']) if first else comment['annotation']
        else:old=comment['annotation']
        changed=[field for field in FIELDS if getattr(a,field)!=old.get(field)]
        if a.label is not None and a.label!=old.get('label') and not a.change_reason.strip():
            raise ValueError('Đổi nhãn AI/nhãn đã lưu cần lý do thay đổi.')
        if changed and a.label is not None and not a.change_reason.strip():
            raise ValueError('Đổi metadata so với nhãn AI/nhãn đã lưu cần lý do trước khi xác nhận.')
        if a.label=='CLEAN' and (a.is_directed_attack or a.is_repeated_attack):
            raise ValueError('CLEAN không thể đồng thời xác nhận công kích; kiểm tra các cờ metadata.')
        super().validate(a,db,corpus)
        if a.is_repeated_attack:
            if a.label!='TOXIC':raise ValueError('Repeated cần nhãn công kích chắc chắn; trường hợp mơ hồ không kết luận lặp.')
            for cid in a.evidence_comment_ids:
                if cid==a.comment_id:continue
                prior=db.execute('SELECT payload_json FROM reviews WHERE thread_id=? AND comment_id=? AND reviewer_id=? AND review_round<=? ORDER BY review_round DESC LIMIT 1',
                  (a.thread_id,cid,a.reviewer_id,a.review_round)).fetchone()
                value=json.loads(prior['payload_json']) if prior else {}
                if value.get('annotation_status') not in DONE or value.get('label')!='TOXIC':
                    raise ValueError('Bằng chứng repeated phải được chính bạn xác nhận TOXIC; bản nháp chưa đủ.')

    def latest(self,reviewer_id):
        if not reviewer_id:return {}
        result={}
        for row in self.list_reviews(reviewer_id=reviewer_id):
            key=(row['thread_id'],row['comment_id'])
            if key not in result or (row['updated_at'],row['review_round'])>(result[key]['updated_at'],result[key]['review_round']):result[key]=row
        return result

    def summaries(self,reviewer_id=None):
        corpus=self.corpus();latest=self.latest(reviewer_id);items=[];reviewed=0;drafts=0
        for t in corpus.values():
            effective=[];count=0
            for c in t['comments']:
                row=latest.get((t['thread_id'],c['comment_id']))
                confirmed=bool(row and row['annotation_status'] in DONE and row['label'])
                count+=confirmed;drafts+=bool(row and row['annotation_status']=='DRAFT')
                effective.append(row['label'] if row and row['label'] else c['annotation']['label'])
            reviewed+=count
            items.append({'thread_id':t['thread_id'],'topic':t['title'],'topic_group':t['topic'],'source_platform':'synthetic',
              'source_url':None,'comments':len(t['comments']),'users':len(t['participants']),'labeled':count,
              'label_counts':{label:effective.count(label) for label in ('CLEAN','TOXIC','UNCERTAIN')}})
        return {'items':items,'progress':{'data_origin':'synthetic','reviewer_id':reviewer_id},
          'counts':{'threads':len(corpus),'comments':sum(len(t['comments']) for t in corpus.values()),'labeled':reviewed,'drafts':drafts}}

    def update_progress(self):
        rows=self.list_reviews();reviewers=sorted({row['reviewer_id'] for row in rows})
        atomic_json(self.root/'manifests/progress.json',{'dataset':'synthetic','updated_at':now(),'human_gold':False,
          'reviewers':{who:self.summaries(who)['counts'] for who in reviewers}})

    def reviewed_records(self,reviewer_id):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',reviewer_id or ''):raise ValueError('Nhập mã người duyệt hợp lệ trước khi xuất.')
        corpus=self.corpus();latest=self.latest(reviewer_id);records=[]
        with self.connect() as db:
            for t in corpus.values():
                for c in t['comments']:
                    row=latest.get((t['thread_id'],c['comment_id']))
                    if not row or row['annotation_status'] not in DONE or row['label'] is None:continue
                    payload={k:v for k,v in row.items() if k not in ('revision','updated_at')}
                    payload['expected_revision']=row['revision']
                    # Verify provenance, round dependencies and repeated evidence again at export.
                    a=self.annotation_model.model_validate(payload);self.validate(a,db,corpus)
                    human={field:row.get(field) for field in FIELDS}
                    human.update(label_source='human_reviewed_synthetic',label_reason=row['reviewer_notes'] or 'Người duyệt đã xác nhận trực tiếp trên giao diện.',
                      reviewer_notes=row['reviewer_notes'],reviewer_id=reviewer_id,review_round=row['review_round'],reviewed_at=row['updated_at'],revision=row['revision'])
                    records.append({'thread_id':t['thread_id'],'topic':t['topic'],'title':t['title'],
                      **{k:c[k] for k in ('comment_id','parent_id','user_id','timestamp','text')},
                      'data_origin':'synthetic','annotation':human,'synthetic_annotation':c['annotation'],
                      'source_sha256':t['source_sha256'],'ai_assisted_review':True,'human_gold':False,'evaluation_eligible':False,
                      'binary_training_candidate':row['label'] in ('CLEAN','TOXIC'),'training_ready':False,
                      'thread_review_complete':all(latest.get((t['thread_id'],item['comment_id']),{}).get('annotation_status') in DONE for item in t['comments']),
                      'context_source':'threads/'+t['thread_id']+'.json','training_performed':False})
        if not records:raise ValueError('Chưa có bình luận được xác nhận; bản nháp/nhãn AI không được xuất thành nhãn đã duyệt.')
        return records

    def lock_evaluation(self,reviewer_id):
        raise ValueError('Synthetic không được khóa thành tập đánh giá thật T028.')
