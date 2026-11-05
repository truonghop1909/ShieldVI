import React,{useCallback,useEffect,useMemo,useRef,useState} from 'react'
import {createRoot} from 'react-dom/client'
import {MessageCircle,ChevronRight,RefreshCw,Home,SquarePen,UserRound} from 'lucide-react'
import {createApi} from './api.js'
import {liveRequest,subscribeLive} from '../../shared/live-transport.mjs'
import './live.css'
import '../../shared/responsive.css'
import './live-responsive.css'
const SESSION='shieldvi-live-session'
const connectionLabel={connected:'Đã kết nối trực tiếp',reconnecting:'Đang kết nối lại',polling:'Đang đồng bộ dự phòng',offline:'Mất kết nối · sẽ thử lại',denied:'Không còn quyền truy cập'}
const analysisLabel={SENDING:'Đang gửi',QUEUED:'Đang phân tích',PROCESSING:'Đang phân tích',COMPLETED:'Đã phân tích',RETRYING:'AI đang thử lại',FAILED:'AI tạm không khả dụng',SUPERSEDED:'Đã có phiên bản mới',NOT_ANALYZED:'Chưa phân tích'}
const when=value=>value?new Date(value).toLocaleString('vi-VN'):'Đang gửi'
const authorName=(row,user)=>row.author_username||(row.author_id===user.id?user.username:`Người dùng ${row.author_id.slice(0,8)}`)

function Login({onLogin}){
 const [username,setUsername]=useState(''),[password,setPassword]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false)
 async function submit(event){event.preventDefault();setBusy(true);setError('');try{const result=await createApi().login({username,password});setPassword('');onLogin(result.access_token)}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <form className="live-login" onSubmit={submit}><h1>ShieldVI · Hội thoại trực tiếp</h1><p>Đăng nhập bằng tài khoản Social hiện có. Tin nhắn được lưu trước khi AI kiểm tra.</p><label>Tên tài khoản<input value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username" required/></label><label>Mật khẩu<input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password" required/></label><button disabled={busy}>Đăng nhập</button>{error&&<p role="alert">{error}</p>}</form>
}

function Conversation({id,token,user,api,onExpired,focusRequest}){
 const [snapshot,setSnapshot]=useState(null),[page,setPage]=useState(1),[connection,setConnection]=useState('reconnecting')
 const [error,setError]=useState(''),[sendError,setSendError]=useState(''),[draft,setDraft]=useState(''),[reply,setReply]=useState(null),[pending,setPending]=useState(null),[sending,setSending]=useState(false)
 const [editing,setEditing]=useState(null),[editBody,setEditBody]=useState(''),[appeal,setAppeal]=useState(null),[reason,setReason]=useState('')
 const scope=useRef(null),retry=useRef(null),refreshTimer=useRef(null),commentInput=useRef(null),focusedRequest=useRef(0)
 function focusComposer(){const input=commentInput.current;if(input){input.focus({preventScroll:true});input.scrollIntoView({block:'center',behavior:'instant'})}}
 useEffect(()=>{
  if(!focusRequest||focusedRequest.current===focusRequest)return
  const frame=requestAnimationFrame(()=>{if(!snapshot){document.getElementById('live-post-detail')?.scrollIntoView({block:'start',behavior:'instant'});return}if(!commentInput.current)return;focusedRequest.current=focusRequest;focusComposer()})
  return()=>cancelAnimationFrame(frame)
 },[focusRequest,snapshot?.post.id])
 const load=useCallback(async signal=>{const data=await liveRequest(`/threads/${id}/snapshot?page=${page}`,token,{signal});if(!signal?.aborted){setSnapshot(data);setError('')}return data},[id,token,page])
 useEffect(()=>{const controller=new AbortController();scope.current=controller;setSnapshot(null);setError('');let stop=()=>{}
  async function resync(){if(controller.signal.aborted)return;try{await load(controller.signal)}catch(e){if(controller.signal.aborted)return;setError(e.message);if([401,403,404].includes(e.status)){setSnapshot(null);if(e.status===401)onExpired();return}clearTimeout(refreshTimer.current);refreshTimer.current=setTimeout(resync,1000)}}
  function requestSync(){clearTimeout(refreshTimer.current);refreshTimer.current=setTimeout(resync,80)}
  window.addEventListener('online',requestSync)
  async function start(){try{await liveRequest(`/threads/${id}/join`,token,{method:'POST',signal:controller.signal});const data=await load(controller.signal)
   stop=subscribeLive(`/threads/${id}/events`,token,{since:data.cursor,threadId:id,signal:controller.signal,onState:setConnection,
    onEvent:requestSync,
    onReset:async()=>{const next=await load(controller.signal);return next.cursor},
    onDenied:status=>{setSnapshot(null);setError('Phiên hoặc quyền xem hội thoại đã thay đổi.');if(status===401)onExpired()}})
  }catch(e){if(!controller.signal.aborted){setError(e.message);setSnapshot(null);if(e.status===401)onExpired()}}}start()
  return()=>{controller.abort();stop();clearTimeout(refreshTimer.current);window.removeEventListener('online',requestSync)}
 },[id,token,load])
 async function send(event){event.preventDefault();if(!draft.trim()||sending)return;setSending(true);setSendError('')
  const parent=reply?.id||null;if(!retry.current||retry.current.body!==draft||retry.current.parent_id!==parent)retry.current={key:crypto.randomUUID(),body:draft,parent_id:parent}
  const attempt=retry.current;setPending({id:`pending:${attempt.key}`,author_id:user.id,body:attempt.body,parent_id:parent,analysis_status:'SENDING',content_revision:0})
  try{const row=await liveRequest(`/threads/${id}/messages`,token,{method:'POST',body:{body:attempt.body,parent_id:parent},key:attempt.key,signal:scope.current.signal});setPending({...row,analysis_status:'QUEUED'});setDraft('');setReply(null);retry.current=null;await load(scope.current.signal)}
  catch(e){if(!scope.current.signal.aborted){setSendError(e.message+' Nội dung vẫn được giữ để thử lại cùng mã gửi.');setPending(null);if(e.status===401)onExpired()}}finally{setSending(false)}
 }
 async function saveEdit(row){try{await api.edit('comments',row,editBody);setEditing(null);await load(scope.current.signal)}catch(e){setSendError(e.message)}}
 async function remove(row){if(!window.confirm('Xóa bình luận này? Nội dung đã xóa sẽ không còn hiển thị.'))return;try{await api.remove('comments',row);await load(scope.current.signal)}catch(e){setSendError(e.message)}}
 async function sendAppeal(row){try{await api.appeal('comment',row,reason);setAppeal(null);setReason('');await load(scope.current.signal)}catch(e){setSendError(e.message)}}
 function chooseReply(row){setReply(row);requestAnimationFrame(focusComposer)}
 const items=snapshot?[...snapshot.comments.items,...(pending&&!snapshot.comments.items.some(x=>x.id===pending.id)?[pending]:[])]:[]
 const composer=<form className="live-composer" aria-label="Soạn bình luận" onSubmit={send}>
  <button type="button" className="comment-focus" aria-controls="live-comment-input" onClick={focusComposer}>Viết bình luận</button>
  {reply&&<div className="reply-banner" data-reply-to-user-id={reply.author_id}>Đang trả lời <span className="user-mention">@{authorName(reply,user)}</span><blockquote>{reply.body}</blockquote><button type="button" onClick={()=>setReply(null)}>Hủy trả lời</button></div>}
  <label htmlFor="live-comment-input">Nội dung tin nhắn</label><textarea id="live-comment-input" ref={commentInput} value={draft} placeholder="Nhập bình luận của bạn tại đây…" maxLength={8000} onChange={e=>setDraft(e.target.value)} rows={3} required/>
  <button type="submit" disabled={sending||!draft.trim()||connection==='denied'}>{sending?'Đang lưu…':'Gửi tin nhắn'}</button>
 </form>
 return <section id="live-post-detail" aria-label="Chi tiết bài đăng"><div className="live-heading"><h2>Bài đăng và bình luận</h2><span role="status" data-testid="live-connection">{connectionLabel[connection]||connection}</span></div><p className="live-muted">Bài {id} · Nội dung chờ kiểm tra chỉ người gửi và moderator được xem.</p>
  {error&&<p role="alert">{error}</p>}{snapshot&&<><div className="live-meta"><strong>{authorName(snapshot.post,user)}</strong><time dateTime={snapshot.post.created_at}>{when(snapshot.post.created_at)}</time></div><p className="live-root">{snapshot.post.body}</p>{composer}<div className="live-messages" aria-live="polite">{items.map(row=><article key={row.id} data-comment-id={row.id} className={[row.author_id===user.id?'own':'',row.parent_id?'is-reply':''].join(' ')}>
   <div className="live-meta"><strong>{authorName(row,user)}</strong><span title={row.analysis_status}>AI: {analysisLabel[row.analysis_status]||row.analysis_status}</span><small>r{row.content_revision} · {row.visibility_status||'Đang gửi'}</small><time dateTime={row.created_at}>{when(row.created_at)}</time></div>
   {row.parent_id&&<details className="reply-context"><summary>Trả lời <span className="user-mention" data-reply-to-user-id={row.reply_to_user_id||''}>@{row.reply_to_username||'người viết bình luận cha'}</span></summary><blockquote>{items.find(parent=>parent.id===row.parent_id)?.body||'Bình luận cha ngoài trang này hoặc chưa được chia sẻ.'}</blockquote></details>}
   {editing===row.id?<label>Sửa nội dung<textarea value={editBody} maxLength={8000} onChange={e=>setEditBody(e.target.value)}/><button onClick={()=>saveEdit(row)}>Lưu thay đổi</button><button onClick={()=>setEditing(null)}>Hủy</button></label>:<p className="live-body">{row.body}</p>}
   {!row.id.startsWith('pending:')&&<div className="live-actions"><button onClick={()=>chooseReply(row)}>Trả lời</button>{row.author_id===user.id&&<><button onClick={()=>{setEditing(row.id);setEditBody(row.body)}}>Sửa</button><button onClick={()=>remove(row)}>Xóa</button>{['HIDDEN','HELD_FOR_REVIEW'].includes(row.visibility_status)&&<button onClick={()=>setAppeal(row.id)}>Kháng nghị</button>}</>}</div>}
   {appeal===row.id&&<div><label>Lý do kháng nghị<textarea value={reason} maxLength={500} onChange={e=>setReason(e.target.value)}/></label><button disabled={!reason.trim()} onClick={()=>sendAppeal(row)}>Gửi kháng nghị</button></div>}
  </article>)}</div><nav aria-label="Phân trang hội thoại"><button disabled={page<=1} onClick={()=>setPage(x=>x-1)}>Trước</button><span>Trang {page} · {snapshot.comments.total} tin có thể xem</span><button disabled={page*50>=snapshot.comments.total} onClick={()=>setPage(x=>x+1)}>Sau</button></nav>
  </>}{!snapshot&&!error&&<p role="status">Đang tải hội thoại…</p>}{sendError&&<p role="alert">{sendError}</p>}
 </section>
}

function Feed({api,user,onSelect,selectedId,token}){
 const [data,setData]=useState(null),[page,setPage]=useState(1),[error,setError]=useState('')
 useEffect(()=>{const controller=new AbortController();let timer,delay=1500,busy=false
  async function refresh(){if(controller.signal.aborted||busy)return;busy=true;clearTimeout(timer)
   try{const signal=AbortSignal.any([controller.signal,AbortSignal.timeout(10000)]);let next
    try{next=await liveRequest(`/feed?page=${page}`,token,{signal})}catch(e){if(e.status!==404)throw e;next=await api.feed(page,signal)}
    if(!controller.signal.aborted){setData(next);setError('');delay=1500}}
   catch(e){if(!controller.signal.aborted){setError(e.message);delay=Math.min(delay*2,8000)}}
   finally{busy=false;if(!controller.signal.aborted)timer=setTimeout(refresh,delay)}}
  setData(null);refresh();window.addEventListener('online',refresh)
  return()=>{controller.abort();clearTimeout(timer);window.removeEventListener('online',refresh)}
 },[api,page,token])
 return <section id="live-feed" className="feed-panel" aria-label="Bảng tin"><div className="feed-heading"><div className="feed-title"><h2>Bảng tin</h2>{data&&<span className="feed-count">{data.total} bài viết</span>}</div><span className="feed-sync"><RefreshCw size={13} aria-hidden="true"/>Tự động cập nhật</span></div><p className="feed-intro">Chọn một bài viết để xem và tham gia bình luận.</p>{error&&<p role="alert">{error}</p>}
  {!data&&!error&&<p role="status">Đang tải bảng tin…</p>}{data?.items.length===0&&<p>Chưa có bài công khai. Bạn có thể đăng bài đầu tiên.</p>}
  <div className="feed-list">{data?.items.map(row=>{const name=authorName(row,user),selected=row.id===selectedId;return <article className={`feed-post${selected?' is-selected':''}`} data-post-id={row.id} key={row.id}><div className="feed-post-heading"><div className="feed-author"><span className="feed-avatar" aria-hidden="true">{name.replace(/^live_/,'').slice(0,2).toUpperCase()}</span><div className="feed-author-info"><strong>{name}</strong><time dateTime={row.created_at} title={when(row.created_at)}>{when(row.created_at)}</time></div></div>{selected&&<span className="feed-selected">Đang xem</span>}</div><p className="live-body">{row.body}</p><div className="feed-post-footer"><button className="feed-open" aria-current={selected?'true':undefined} onClick={()=>onSelect(row.id)}><MessageCircle size={16} aria-hidden="true"/><span>Xem bài và bình luận</span><ChevronRight size={16} aria-hidden="true"/></button></div></article>})}</div>
  {data&&(data.total>data.page_size||page>1)&&<nav aria-label="Phân trang bảng tin"><button disabled={page<=1} onClick={()=>setPage(p=>p-1)}>Bài trước</button><span>Trang {page} · {data.total} bài</span><button disabled={page*data.page_size>=data.total} onClick={()=>setPage(p=>p+1)}>Bài sau</button></nav>}
 </section>
}

function LiveApp(){
 const [token,setToken]=useState(()=>sessionStorage.getItem(SESSION)||''),[user,setUser]=useState(null),[id,setId]=useState(()=>new URLSearchParams(location.search).get('thread')||''),[input,setInput]=useState(()=>new URLSearchParams(location.search).get('thread')||'')
 const [error,setError]=useState(''),[title,setTitle]=useState(''),[creating,setCreating]=useState(false),[focusRequest,setFocusRequest]=useState(0)
 const postRetry=useRef(null),sessionScope=useRef(null)
 const expired=useCallback(()=>{sessionStorage.removeItem(SESSION);setToken('');setUser(null);setId('')},[])
 const api=useMemo(()=>createApi(token,expired),[token,expired])
 useEffect(()=>{const url=new URL(location.href);if(id)url.searchParams.set('thread',id);else url.searchParams.delete('thread');history.replaceState(null,'',url)},[id])
 useEffect(()=>{if(!token)return;const controller=new AbortController();sessionScope.current=controller;api.me(controller.signal).then(setUser).catch(e=>{if(e.name!=='AbortError'){setError(e.message);expired()}});return()=>controller.abort()},[api,token,expired])
 function login(value){sessionStorage.setItem(SESSION,value);setToken(value);setError('')}
 function openPost(value){setInput(value);setId(value);setError('');setFocusRequest(n=>n+1)}
 async function create(event){event.preventDefault();if(!title.trim()||creating)return;setCreating(true);setError('')
  if(!postRetry.current||postRetry.current.body!==title)postRetry.current={body:title,key:crypto.randomUUID()}
  const signal=sessionScope.current.signal
  try{const row=await api.createPost(postRetry.current.body,postRetry.current.key);if(signal.aborted)return;openPost(row.id);setTitle('');postRetry.current=null}catch(e){if(!signal.aborted)setError(e.message)}finally{setCreating(false)}}
 if(!token)return <Login onLogin={login}/>
 return <main className="live-app"><a className="ui-skip" href="#live-content">Đến nội dung chính</a><header><div><b>ShieldVI · Bảng tin</b><p>Đăng bài · Bình luận và trả lời trực tiếp · Kiểm duyệt AI</p></div><button onClick={async()=>{try{await api.logout()}finally{expired()}}}>Đăng xuất</button></header>
  {!user?<p role="status">Đang xác minh phiên…</p>:<div className="live-layout"><nav className="live-nav" aria-label="Điều hướng Social"><span className="live-nav-label">KHÔNG GIAN CỦA BẠN</span><a href="#live-feed"><Home size={20} aria-hidden="true"/>Bảng tin</a><a href="#live-create"><SquarePen size={20} aria-hidden="true"/>Đăng bài</a><a href={id?'#live-post-detail':'#live-join'}><MessageCircle size={20} aria-hidden="true"/>Hội thoại</a><a href="#live-account"><UserRound size={20} aria-hidden="true"/>Tài khoản</a></nav><div id="live-content" className="live-content"><p>Xin chào <strong>{user.username}</strong></p><section id="live-create"><form onSubmit={create}><h2>Đăng bài</h2><label>Nội dung bài đăng<textarea value={title} maxLength={8000} onChange={e=>setTitle(e.target.value)} placeholder="Chia sẻ câu chuyện của bạn…" required/></label><button disabled={creating||!title.trim()}>{creating?'Đang đăng…':'Đăng bài'}</button><p>Bài chờ phân tích chỉ bạn và moderator xem được; bài công khai sẽ xuất hiện trên bảng tin của mọi người.</p></form></section>
  <Feed api={api} user={user} onSelect={openPost} selectedId={id} token={token}/>
  <details id="live-join" className="live-join"><summary>Mở bài bằng mã được chia sẻ</summary><label>Mã hội thoại<input value={input} onChange={e=>setInput(e.target.value)} placeholder="Post ID"/></label><button onClick={()=>openPost(input.trim())} disabled={!input.trim()}>Vào hội thoại</button></details>
  {id&&<Conversation key={id} id={id} token={token} user={user} api={api} onExpired={expired} focusRequest={focusRequest}/>}<section id="live-account" className="account-card" aria-label="Thông tin tài khoản"><h2>Tài khoản của bạn</h2><dl><dt>Tên hiển thị</dt><dd>{user.username}</dd><dt>Vai trò</dt><dd>{user.role}</dd></dl></section></div><aside className="live-help"><h2>Trò chuyện có trách nhiệm</h2><p>Góp ý về nội dung, tôn trọng người tham gia.</p><p>Dùng Trả lời để giữ đúng ngữ cảnh. AI đưa ra tín hiệu tham khảo; moderator quyết định kiểm duyệt.</p></aside></div>}{error&&<p role="alert">{error}</p>}
 </main>
}
createRoot(document.getElementById('root')).render(<LiveApp/> )
