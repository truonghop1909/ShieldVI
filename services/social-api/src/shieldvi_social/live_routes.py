"""Authenticated public-thread membership + minimal durable SSE/polling."""
import asyncio,time
from uuid import UUID
from fastapi import APIRouter,Depends,Header,HTTPException,Query,Request,Response
from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool
from sqlalchemy import select,func,delete
from .dependencies import bearer,authenticate,content_writer,get_content_write_db
from .content_routes import create_comment,comments,must_read,feed as canonical_feed
from .content_schemas import CommentCreate
from .content_store import output,privileged
from .models import Post,User,AuthSession,ModerationJob
from .live_store import LiveEvent,LiveMember,envelope
from .live_contract import status_for
from .live_identity import identities
router=APIRouter(prefix='/api/live',tags=['live-conversations'])

def principal(request:Request,credentials=Depends(bearer)):
    # Never keep an auth read transaction open for a streaming response.
    with request.app.state.sessions() as db:return authenticate(credentials,db)

def access(db,post_id,user,member=True):
    post=must_read(db.get(Post,post_id),user,db)
    if post.visibility_status=='DELETED_BY_AUTHOR':raise HTTPException(404,'Content not found')
    if member and not privileged(user) and db.get(LiveMember,(post_id,user.id)) is None:
        raise HTTPException(403,'Thread membership required')
    return post

@router.get('/feed')
def feed(request:Request,page:int=Query(1,ge=1,le=10000),who=Depends(principal)):
    with request.app.state.sessions() as db:
        data=canonical_feed(page,10,who,db)
        data['items']=identities(db,data['items'],who.user)
        return data

@router.post('/threads/{post_id}/join')
def join(post_id:UUID,request:Request,who=Depends(principal)):
    with request.app.state.sessions() as db:
        if db.bind.dialect.name=='sqlite':db.connection(execution_options={'sqlite_immediate':True})
        access(db,str(post_id),who.user,False)
        if db.get(LiveMember,(str(post_id),who.user.id)) is None:db.add(LiveMember(thread_id=str(post_id),user_id=who.user.id))
        db.commit()
    return {'thread_id':str(post_id),'joined':True}

@router.delete('/threads/{post_id}/join')
def leave(post_id:UUID,request:Request,who=Depends(principal)):
    with request.app.state.sessions() as db:
        db.execute(delete(LiveMember).where(LiveMember.thread_id==str(post_id),LiveMember.user_id==who.user.id));db.commit()
    return {'joined':False}

@router.post('/threads/{post_id}/messages',status_code=201)
def send(post_id:UUID,payload:CommentCreate,request:Request,response:Response,idempotency_key:UUID=Header(alias='Idempotency-Key'),
         who=Depends(content_writer),db=Depends(get_content_write_db)):
    access(db,str(post_id),who.user)
    if not privileged(who.user):db.info['live_membership_required']=(str(post_id),who.user.id)
    row=create_comment(post_id,payload,request,response,idempotency_key,who,db)
    return identities(db,[row],who.user)[0]

@router.get('/threads/{post_id}/snapshot')
def snapshot(post_id:UUID,request:Request,page:int=Query(1,ge=1,le=10000),who=Depends(principal)):
    with request.app.state.sessions() as db:
        post=access(db,str(post_id),who.user)
        data=comments(post_id,page,50,who,db)
        jobs=db.scalars(select(ModerationJob).where(ModerationJob.entity_type=='comment',ModerationJob.entity_id.in_([r['id'] for r in data['items']]))).all() if data['items'] else []
        latest={}
        for job in jobs:
            if job.entity_id not in latest or job.content_revision>latest[job.entity_id].content_revision:latest[job.entity_id]=job
        for row in data['items']:row['analysis_status']=status_for(latest.get(row['id']))
        data['items']=identities(db,data['items'],who.user)
        cursor=db.scalar(select(func.max(LiveEvent.id)).where(LiveEvent.thread_id==str(post_id))) or 0
        return {'post':identities(db,[output(post,who.user)],who.user)[0],'comments':data,'cursor':cursor,'schema_version':'live-1.0','identity_version':'live-identity-1.0'}

def read_page(request,who,post_id,since,staff=False):
    with request.app.state.sessions() as db:
        session=db.get(AuthSession,who.session.token_hash);user=db.get(User,who.user.id)
        if not session or session.expires_at<=int(time.time()) or not user or user.status!='active':raise HTTPException(401,'Invalid or expired credentials')
        if staff:
            if not privileged(user):raise HTTPException(403,'Staff required')
        else:access(db,post_id,user)
        maximum=db.scalar(select(func.max(LiveEvent.id))) or 0
        if since>maximum:raise HTTPException(409,'Cursor ahead of log; reload snapshot')
        query=select(LiveEvent).where(LiveEvent.id>since)
        if not staff:query=query.where(LiveEvent.thread_id==post_id)
        rows=db.scalars(query.order_by(LiveEvent.id).limit(101)).all()
        return {'items':[envelope(row).model_dump(mode='json') for row in rows[:100]],
                'cursor':rows[min(len(rows),100)-1].id if rows else since,'has_more':len(rows)>100}

@router.get('/threads/{post_id}/events/poll')
def poll(post_id:UUID,request:Request,since:int=Query(0,ge=0,le=9223372036854775807),who=Depends(principal)):
    return read_page(request,who,str(post_id),since)

def stream_response(request,who,post_id,since,once,staff=False):
    if any(k in request.query_params for k in ('token','access_token','authorization')):raise HTTPException(400,'Credentials must use Authorization header')
    header=request.headers.get('Last-Event-ID')
    if header:
        if not header.isdigit() or len(header)>18:raise HTTPException(422,'Invalid cursor')
        since=max(since,int(header))
    initial=read_page(request,who,post_id,since,staff)
    async def events():
        page=initial;cursor=since;start=time.monotonic()
        while True:
            for item in page['items']:
                cursor=item['event_id']
                yield f"id: {cursor}\nevent: {item['event_type']}\ndata: "+__import__('json').dumps(item,separators=(',',':'))+'\n\n'
            if once or time.monotonic()-start>=25 or await request.is_disconnected():break
            if not page['items']:yield ': heartbeat\n\n'
            await asyncio.sleep(.25)
            # A checkout/SQLite lock wait must not block ASGI scheduling:
            # other requests need the event loop to release their DB sessions.
            try:page=await run_in_threadpool(read_page,request,who,post_id,cursor,staff)
            except HTTPException:break
    return StreamingResponse(events(),media_type='text/event-stream',headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})

@router.get('/threads/{post_id}/events')
def stream(post_id:UUID,request:Request,since:int=Query(0,ge=0,le=9223372036854775807),once:bool=False,who=Depends(principal)):
    return stream_response(request,who,str(post_id),since,once)

@router.get('/moderator/events')
def moderator_stream(request:Request,since:int=Query(0,ge=0,le=9223372036854775807),once:bool=False,who=Depends(principal)):
    return stream_response(request,who,None,since,once,True)

@router.get('/moderator/events/poll')
def moderator_poll(request:Request,since:int=Query(0,ge=0,le=9223372036854775807),who=Depends(principal)):
    return read_page(request,who,None,since,True)
