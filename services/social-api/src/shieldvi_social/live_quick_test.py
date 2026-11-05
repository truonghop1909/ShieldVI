"""Private bounded in-memory staff tests; no Social content/dataset writes."""
import json,secrets,threading,time
from dataclasses import replace
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import Field,model_validator
from .moderation_contract import ContractModel,ContextComment,ModerationRequest,OpaqueId
from .live_ai_client import LiveAIClient
from .ai_client import WorkerSettings,AIError
from .review_routes import staff_reader

class QuickConversation(ContractModel):
    thread_id:OpaqueId
    profile:Literal['conservative']='conservative'
    comments:list[ContextComment]=Field(min_length=1,max_length=50)

    @model_validator(mode='after')
    def graph(self):
        seen=set();previous=None
        if sum(len(c.text) for c in self.comments)>64000:raise ValueError('Conversation exceeds text budget')
        for row in self.comments:
            if row.comment_id in seen or row.parent_id and row.parent_id not in seen:raise ValueError('Duplicate ID or parent must precede reply')
            if previous and row.timestamp<previous:raise ValueError('Comments must be chronological')
            seen.add(row.comment_id);previous=row.timestamp
        self.payload(len(self.comments)-1,'validation')
        return self

    def payload(self,index,job_id):
        row=self.comments[index]
        return ModerationRequest(schema_version='1.0',request_id=f'quick_{job_id}_{index}',content_id=row.comment_id,
            content_revision=1,user_id=row.user_id,text=row.text,timestamp=row.timestamp,parent_id=row.parent_id,
            mentioned_user_ids=row.mentioned_user_ids,context={'post_id':self.thread_id,'source':'social-api','complete':True,
                'recent_comments':[c.model_dump() for c in self.comments[:index]]})

class QuickTests:
    def __init__(self,client_factory=LiveAIClient,deadline=120):
        self.client_factory=client_factory;self.deadline=deadline;self.lock=threading.RLock();self.jobs={};self.running=False;self.thread=None

    def close(self):
        with self.lock:
            for job in self.jobs.values():job['cancel'].set()
        if self.thread and self.thread.is_alive():self.thread.join(timeout=2)

    def purge(self):
        cutoff=time.monotonic()-1800
        self.jobs={key:job for key,job in self.jobs.items() if job['created']>=cutoff or job['status'] in ('QUEUED','RUNNING','CANCELLING')}

    def create(self,owner,payload,settings):
        with self.lock:
            self.purge()
            if self.running:raise HTTPException(429,'A test is already running',headers={'Retry-After':'2'})
            if len(self.jobs)>=16:
                oldest=next(iter(self.jobs));del self.jobs[oldest]
            identity=secrets.token_hex(16);job={'id':identity,'owner':owner,'created':time.monotonic(),'status':'QUEUED',
                'completed':0,'total':len(payload.comments),'result':None,'error':None,'cancel':threading.Event()}
            self.jobs[identity]=job;self.running=True
            self.thread=threading.Thread(target=self.run,args=(job,payload,settings),daemon=True);self.thread.start()
            return self.public(job)

    def public(self,job):return {key:job[key] for key in ('id','status','completed','total','result','error')}

    def get(self,identity,owner,cancel=False):
        with self.lock:
            self.purge();job=self.jobs.get(identity)
            if not job or job['owner']!=owner:raise HTTPException(404,'Test not found')
            if cancel and job['status'] in ('QUEUED','RUNNING','CANCELLING'):
                job['cancel'].set();job['status']='CANCELLING'
            return self.public(job)

    def run(self,job,payload,settings):
        client=None;started=time.monotonic()
        try:
            client=self.client_factory(settings);rows=[];events={};fingerprint=None
            with self.lock:job['status']='RUNNING'
            for index,row in enumerate(payload.comments):
                if job['cancel'].is_set():break
                if time.monotonic()-started>self.deadline:raise AIError('TEST_DEADLINE',False)
                response=client.moderate(payload.payload(index,job['id']))
                sig=response.conversation_signals
                if sig.processor!='default-v5' or response.model_threshold!=.41:raise AIError('UNAPPROVED_MODEL_CONFIGURATION',False)
                if fingerprint and fingerprint!=sig.model_fingerprint:raise AIError('MODEL_CHANGED_DURING_TEST',False)
                fingerprint=sig.model_fingerprint
                item={**row.model_dump(mode='json'),'analysis':response.model_dump(mode='json')};rows.append(item)
                for event in response.evidence:
                    value=event.model_dump(mode='json');events[(event.actor_user_id,event.target_user_id)]=value
                if len(json.dumps(rows,ensure_ascii=False).encode('utf-8'))>4194304:raise AIError('TEST_RESULT_TOO_LARGE',False)
                with self.lock:job['completed']=len(rows)
            with self.lock:
                if job['cancel'].is_set():job['status']='CANCELLED'
                else:
                    job['result']={'schema_version':'quick-test-1.0','thread_id':payload.thread_id,'scope':'manual_test_not_human_gold',
                        'model_version':rows[-1]['analysis']['model_version'],'threshold':.41,'processor':'default-v5',
                        'model_fingerprint':fingerprint,'comments':rows,'repeated_events':list(events.values()),
                        'elapsed_ms':round((time.monotonic()-started)*1000,2),'content_saved':False,'training_performed':False}
                    job['status']='COMPLETED'
        except Exception as error:
            with self.lock:
                job['status']='CANCELLED' if job['cancel'].is_set() else 'FAILED'
                job['error']=error.code if isinstance(error,AIError) else 'TEST_FAILED'
        finally:
            if client:
                try:client.close()
                except Exception:pass
            with self.lock:self.running=False

router=APIRouter(prefix='/api/live/moderator/test-conversations',tags=['staff-ai-tests'])

@router.post('',status_code=202)
def create(payload:QuickConversation,request:Request,who=Depends(staff_reader)):
    try:settings=WorkerSettings.from_env();settings=replace(settings,read_timeout=min(settings.read_timeout,15))
    except ValueError:raise HTTPException(503,'AI test service is not configured') from None
    return request.app.state.quick_tests.create(who.user.id,payload,settings)

@router.get('/{identity}')
def get(identity:str,request:Request,who=Depends(staff_reader)):
    return request.app.state.quick_tests.get(identity,who.user.id)

@router.delete('/{identity}')
def cancel(identity:str,request:Request,who=Depends(staff_reader)):
    return request.app.state.quick_tests.get(identity,who.user.id,cancel=True)
