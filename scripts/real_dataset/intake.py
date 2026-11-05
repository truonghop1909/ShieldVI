"""Local anonymized quarantine for user-supplied threads, never automatic real gold."""
from pathlib import Path
from urllib.parse import urlsplit
from pydantic import BaseModel,Field,AwareDatetime,ConfigDict,model_validator
from .core import Pseudonymizer,atomic_json,sha_bytes,now

class ManualComment(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source_comment_id:str=Field(min_length=1,max_length=200)
    parent_source_comment_id:str|None=Field(default=None,max_length=200)
    source_user_id:str|None=Field(default=None,max_length=300)
    timestamp:AwareDatetime|None=None
    text:str=Field(min_length=1,max_length=8000)

class ManualThread(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source_url:str=Field(min_length=1,max_length=2000)
    license_declaration:str=Field(min_length=1,max_length=300)
    license_evidence_url:str|None=Field(default=None,max_length=2000)
    collected_at:AwareDatetime|None=None
    topic:str=Field(default='',max_length=300)
    comments:list[ManualComment]=Field(min_length=1,max_length=500)
    @model_validator(mode='after')
    def structure(self):
        for value in (self.source_url,self.license_evidence_url):
            if value and (urlsplit(value).scheme!='https' or not urlsplit(value).hostname):raise ValueError('HTTPS provenance URL required')
        lookup={c.source_comment_id:c for c in self.comments}
        if len(lookup)!=len(self.comments):raise ValueError('Duplicate source comment ID')
        for c in self.comments:
            seen={c.source_comment_id};parent=c.parent_source_comment_id
            while parent:
                if parent not in lookup:raise ValueError('Missing source parent')
                if parent in seen:raise ValueError('Parent cycle')
                seen.add(parent);parent=lookup[parent].parent_source_comment_id
        return self

def stage_manual_thread(data_root,payload):
    import json
    root=Path(data_root)
    if (root/'manifests/evaluation_lock.json').exists():raise ValueError('Evaluation locked; use a new dataset version')
    draft=ManualThread.model_validate(payload)
    raw=draft.model_dump(mode='json');fingerprint=sha_bytes(json.dumps(raw,sort_keys=True,ensure_ascii=False).encode())
    ident='M_'+fingerprint[:24];path=root/'anonymized/manual_inbox'/(ident+'.json')
    if path.exists():return {'intake_id':ident,'status':'PENDING_SOURCE_PRIVACY_REVIEW','already_present':True,'counted_as_real':False}
    anon=Pseudonymizer(root);host=urlsplit(draft.source_url).hostname;authors=[c.source_user_id for c in draft.comments if c.source_user_id]
    ids={c.source_comment_id:'C_'+sha_bytes((ident+'|'+c.source_comment_id).encode())[:24] for c in draft.comments}
    comments=[]
    for c in draft.comments:
        text,redactions=anon.redact(c.text,host,authors)
        comments.append({'comment_id':ids[c.source_comment_id],'parent_id':ids.get(c.parent_source_comment_id),
          'user_id':anon.user(host,c.source_user_id),'timestamp':c.timestamp.isoformat() if c.timestamp else None,'text':text,
          'timestamp_origin':'user_supplied_unverified' if c.timestamp else 'missing_from_source','parent_origin':'user_supplied_unverified','redactions':redactions})
    topic,_=anon.redact(draft.topic,host,authors)
    value={'intake_id':ident,'received_at':now(),'source_url':draft.source_url,'source_platform':host,
      'license_declaration':draft.license_declaration,'license_evidence_url':draft.license_evidence_url,
      'source_input_sha256':fingerprint,'collected_at':draft.collected_at.isoformat() if draft.collected_at else None,
      'topic':topic,'comments':comments,'status':'PENDING_SOURCE_PRIVACY_REVIEW','data_origin':'user_supplied_unverified',
      'source_permission_status':'UNVERIFIED','human_gold':False,'evaluation_eligible':False,'training_eligible':False,
      'labels':None,'source_receipt_verified':False,'promotion_requires':'Verified source/rights receipt and supported source adapter, privacy and leakage checks; then human Round1/Round2.'}
    atomic_json(path,value)
    return {'intake_id':ident,'status':value['status'],'already_present':False,'counted_as_real':False,'comments':len(comments)}
