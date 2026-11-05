const configured=(import.meta.env?.VITE_SOCIAL_API_BASE||'').trim()
if(configured){const u=new URL(configured);if(!['http:','https:'].includes(u.protocol)||u.username||u.password||u.pathname!=='/'||u.search||u.hash)throw new Error('API origin must be exact HTTP(S)')}
const base=configured.replace(/\/$/,'')
export class LiveError extends Error{constructor(status,message){super(message);this.status=status}}
function headers(token,json=false){return {Authorization:`Bearer ${token}`,Accept:json?'application/json':'text/event-stream',...(json?{'Content-Type':'application/json'}:{})}}
export async function liveRequest(path,token,{method='GET',body,key,signal}={}){
 const response=await fetch(`${base}/api/live${path}`,{method,headers:{...headers(token,true),...(key?{'Idempotency-Key':key}:{})},credentials:'omit',redirect:'error',cache:'no-store',
  signal:AbortSignal.any([signal,AbortSignal.timeout(15000)].filter(Boolean)),body:body===undefined?undefined:JSON.stringify(body)})
 if(!response.ok)throw new LiveError(response.status,({401:'Phiên đăng nhập hết hạn.',403:'Bạn chưa có quyền tham gia.',404:'Hội thoại không còn được chia sẻ.',409:'Phiên bản đã đổi; hãy tải snapshot mới.',429:'Thao tác quá nhanh, vui lòng thử lại.'})[response.status]||'Máy chủ chưa xử lý được yêu cầu.')
 return response.json()
}
export function acceptEvent(event,state){
 if(event.schema_version!=='live-1.0'||!Number.isSafeInteger(event.event_id)||event.event_id<1||!Number.isInteger(event.content_revision)||event.content_revision<1||!Number.isInteger(event.decision_version)||event.decision_version<0)throw new Error('Invalid event envelope')
 if(state.threadId&&event.thread_id!==state.threadId)throw new Error('Unexpected thread')
 if(event.event_id<=state.cursor)return false
 state.cursor=event.event_id
 const key=`${event.thread_id}:${event.content_id}`,prior=state.versions.get(key),version=[event.content_revision,event.decision_version]
 if(prior&&(version[0]<prior[0]||(version[0]===prior[0]&&version[1]<prior[1])))return false
 state.versions.set(key,version);if(state.versions.size>1000)state.versions.delete(state.versions.keys().next().value)
 return true
}
function pause(ms,signal){return new Promise(resolve=>{const done=()=>{clearTimeout(timer);signal.removeEventListener('abort',done);resolve()};const timer=setTimeout(done,ms);signal.addEventListener('abort',done,{once:true});if(signal.aborted)done()})}
export function subscribeLive(path,token,{since=0,threadId,onEvent,onState=()=>{},onDenied=()=>{},onReset=async()=>0,signal}={}){
 const controller=new AbortController(),stop=()=>controller.abort(),state={cursor:since,threadId,versions:new Map()}
 signal?.addEventListener('abort',stop,{once:true});if(signal?.aborted)stop()
 const emit=event=>{if(acceptEvent(event,state))onEvent?.(event)}
 async function run(){let delay=500
  while(!controller.signal.aborted){
   try{
    onState('reconnecting')
    const response=await fetch(`${base}/api/live${path}?since=${state.cursor}`,{headers:headers(token),credentials:'omit',redirect:'error',cache:'no-store',signal:AbortSignal.any([controller.signal,AbortSignal.timeout(35000)])})
    if([401,403,404].includes(response.status)){onState('denied');onDenied(response.status);break}
    if(response.status===409){state.cursor=await onReset();continue}
    if(!response.ok||!response.body)throw new Error('Stream unavailable')
    onState('connected');delay=500
    const reader=response.body.getReader(),decoder=new TextDecoder();let buffer=''
    while(!controller.signal.aborted){const {done,value}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});buffer=buffer.replace(/\r\n/g,'\n');if(buffer.length>1048576)throw new Error('Event buffer exceeded')
     let end;while((end=buffer.indexOf('\n\n'))>=0){const frame=buffer.slice(0,end);buffer=buffer.slice(end+2);const data=frame.split('\n').filter(l=>l.startsWith('data:')).map(l=>l.slice(5).trim()).join('\n');if(data)emit(JSON.parse(data))}}
    await pause(80,controller.signal)
   }catch(error){if(controller.signal.aborted)break
    onState('polling')
    try{const data=await liveRequest(`${path}/poll?since=${state.cursor}`,token,{signal:controller.signal});for(const event of data.items)emit(event)}
    catch(error){if([401,403,404].includes(error.status)){onState('denied');onDenied(error.status);break}if(error.status===409)state.cursor=await onReset();else onState('offline')}
    await pause(delay,controller.signal);delay=Math.min(30000,delay*2)
   }
  }
  signal?.removeEventListener('abort',stop)
 }
 run().catch(()=>{if(!controller.signal.aborted)onState('offline')});return stop
}
