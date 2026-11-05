import React,{useCallback,useEffect,useRef,useState} from 'react'
import {ShieldCheck,Inbox,Flag,Scale,AlertTriangle,RefreshCw,LogOut,ArrowUpRight} from 'lucide-react'
import {apiClient,versions} from './api.js'

const tabs=[['review','Cần xem xét',Inbox],['reports','Báo cáo',Flag],['appeals','Kháng nghị',Scale],['failed','AI lỗi',AlertTriangle],['all','Tất cả',ShieldCheck]]
export const fmt=value=>value?new Date(typeof value==='number'?value*1000:value).toLocaleString('vi-VN'):'—'
export const label=state=>({PENDING_MODERATION:'Chờ kiểm tra',PUBLISHED:'Đã công khai',PUBLISHED_FLAGGED:'Công khai · cần xem xét',HIDDEN:'Đang ẩn',HELD_FOR_REVIEW:'Đang giữ',DELETED_BY_AUTHOR:'Tác giả đã xóa'}[state]||state)
export function ErrorBox({error}){return error?<p className="error" role="alert">{error}</p>:null}
function Brand(){return <div className="brand"><ShieldCheck size={27}/><div>Shield<span>VI</span><small>KHÔNG GIAN KIỂM DUYỆT</small></div></div>}
export function Pager({data,setPage}){return data&&data.total>data.page_size?<nav className="pager" aria-label="Phân trang"><button disabled={data.page===1} onClick={()=>setPage(data.page-1)}>Trước</button><span>Trang {data.page} / {Math.ceil(data.total/data.page_size)}</span><button disabled={data.page*data.page_size>=data.total} onClick={()=>setPage(data.page+1)}>Sau</button></nav>:null}

function Login({onLogin,notice}){
  const [username,setUsername]=useState(''),[password,setPassword]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false)
  const pending=useRef(null)
  useEffect(()=>()=>pending.current?.abort(),[])
  async function submit(event){
    event.preventDefault();if(busy)return
    const c=new AbortController();pending.current=c;setBusy(true);setError('')
    try{
      const result=await apiClient()('/auth/login',{method:'POST',body:{username,password},signal:c.signal})
      const api=apiClient(result.access_token),user=await api('/me',{signal:c.signal})
      if(!['admin','moderator'].includes(user.role)){await api('/auth/logout',{method:'POST',signal:c.signal});throw new Error('Chỉ tài khoản admin hoặc moderator được truy cập.')}
      if(!c.signal.aborted){setPassword('');onLogin({...result,user,expiresAt:Date.now()+result.expires_in*1000})}
    }catch(e){if(e.name!=='AbortError')setError(e.message)}finally{if(!c.signal.aborted)setBusy(false)}
  }
  return <main className="login"><Brand/><section className="login-card"><span className="eyebrow">CON NGƯỜI QUYẾT ĐỊNH</span><h1>Giữ cuộc trò chuyện<br/>đáng để tham gia.</h1><p>Đọc ngữ cảnh, lắng nghe kháng nghị và đưa ra quyết định có lý do.</p>{notice&&<p role="status">{notice}</p>}<ErrorBox error={error}/><form onSubmit={submit}><label>Tên tài khoản<input autoComplete="username" required value={username} onChange={e=>setUsername(e.target.value)} disabled={busy}/></label><label>Mật khẩu<input type="password" autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)} disabled={busy}/></label><button className="primary" disabled={busy}>{busy?'Đang đăng nhập…':'Đăng nhập kiểm duyệt'}<ArrowUpRight size={17}/></button></form><small>Phiên chỉ lưu trong bộ nhớ. Tải lại trang cần đăng nhập lại.</small></section><p className="login-note">AI cung cấp tín hiệu. Quyết định cần ngữ cảnh và trách nhiệm.</p></main>
}

import ReviewDetail from './ReviewDetail.jsx'
function Dashboard({session,onExpired,onLogout}){
  const scope=useRef(null)
  useEffect(()=>{const c=new AbortController();scope.current=c;return()=>c.abort()},[])
  const api=useCallback((path,opts={})=>apiClient(session.access_token,onExpired,scope.current?.signal)(path,opts),[session.access_token,onExpired])
  const [tab,setTab]=useState('review'),[type,setType]=useState('all'),[page,setPage]=useState(1),[data,setData]=useState(null),[stats,setStats]=useState(null),[version,refresh]=useState(0),[selected,setSelected]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false)
  useEffect(()=>{const c=new AbortController();setData(null);setError('');Promise.all([api(`/moderation/queue?tab=${tab}&entity_type=${type}&page=${page}&page_size=10`,{signal:c.signal}),api('/moderation/jobs',{signal:c.signal})]).then(([rows,stats])=>{setData(rows);setStats(stats)}).catch(e=>{if(e.name!=='AbortError')setError(e.message)});return()=>c.abort()},[api,tab,type,page,version])
  async function logout(){setBusy(true);try{await api('/auth/logout',{method:'POST'});scope.current?.abort();onLogout()}catch(e){if(e.name!=='AbortError')setError(e.message)}finally{setBusy(false)}}
  return <div><a className="skip" href="#main">Đến nội dung chính</a><header><Brand/><div className="account"><span>{session.user.username}<small>{session.user.role}</small></span><button onClick={logout} disabled={busy} aria-label="Đăng xuất"><LogOut size={18}/></button></div></header><div className="workspace"><aside><p className="eyebrow">BÀN LÀM VIỆC</p><nav aria-label="Hàng chờ kiểm duyệt">{tabs.map(([id,name,Icon])=><button key={id} className={tab===id?'active':''} aria-current={tab===id?'page':undefined} onClick={()=>{setTab(id);setPage(1);setSelected(null)}}><Icon size={18}/>{name}</button>)}</nav><div className="policy-note"><ShieldCheck size={24}/><strong>Ngữ cảnh trước.<br/>Quyết định sau.</strong><p>AI chỉ đưa ra tín hiệu. Cảnh báo không đồng nghĩa vi phạm.</p><small>Shadow · HIGH auto-hold tắt</small></div></aside><main id="main"><div className="page-title"><div><p className="eyebrow">KIỂM DUYỆT CÓ TRÁCH NHIỆM</p><h1>Mỗi quyết định,<br className="mobile-break"/> một lời giải thích.</h1><p className="muted">Đọc toàn văn. Đối chiếu bằng chứng. Giữ lại lịch sử.</p></div><button className="refresh" onClick={()=>refresh(v=>v+1)}><RefreshCw size={16}/>Làm mới hàng chờ</button></div><section className="metrics" aria-label="Tình trạng worker"><div><small>JOB ĐANG CHỜ</small><strong>{stats?.queue_size??'—'}</strong></div><div><small>AI GẦN ĐÂY</small><strong className="metric-text">{stats?.model_availability||'Chưa rõ'}</strong></div><div><small>CHỜ LÂU NHẤT</small><strong>{stats?.oldest_wait_seconds??'—'}<small> giây</small></strong></div></section><ErrorBox error={error}/><div className="desk"><section className="queue" aria-label="Danh sách hàng chờ"><div className="section-title"><h2>{tabs.find(t=>t[0]===tab)[1]} <span>{data?.total??'—'}</span></h2><label className="filter-label">Loại nội dung<select value={type} onChange={e=>{setType(e.target.value);setPage(1);setSelected(null)}}><option value="all">Tất cả</option><option value="post">Bài viết</option><option value="comment">Bình luận</option></select></label></div>{!data&&!error&&<p role="status">Đang tải hàng chờ…</p>}{data?.items.length===0&&<div className="empty"><Inbox size={34}/><h3>Hàng chờ đã gọn.</h3><p>Không có nội dung trong bộ lọc này.</p></div>}{data?.items.map(item=><button className={`queue-item ${selected?.content.id===item.content.id?'selected':''}`} key={item.content.id} onClick={()=>setSelected(item)}><span className="item-top">{item.entity_type==='post'?'BÀI VIẾT':'BÌNH LUẬN'}<span>Ưu tiên {item.priority+1}</span></span><span className="preview">{item.content.body}</span><span className="pill">{label(item.content.visibility_status)}</span><span className="item-bottom">{fmt(item.content.created_at)} · {item.report_count} báo cáo</span></button>)}<Pager data={data} setPage={setPage}/></section>{selected?<ReviewDetail key={selected.content.id} selected={selected} api={api} user={session.user} onMutate={()=>refresh(v=>v+1)}/>:<section className="select-prompt"><Scale size={39}/><h2>Một góc nhìn đầy đủ hơn.</h2><p>Chọn nội dung trong hàng chờ để xem toàn văn, ngữ cảnh và lịch sử.</p></section>}</div></main></div></div>
}

export default function App(){
  const [session,setSession]=useState(null),[notice,setNotice]=useState('')
  const expired=useCallback(()=>{setSession(null);setNotice('Phiên đã hết hạn. Vui lòng đăng nhập lại.')},[])
  useEffect(()=>{if(!session)return;const timer=setTimeout(expired,Math.max(0,session.expiresAt-Date.now()));return()=>clearTimeout(timer)},[session,expired])
  return session?<Dashboard key={session.access_token} session={session} onExpired={expired} onLogout={()=>{setSession(null);setNotice('Đã đăng xuất.')}}/>:<Login notice={notice} onLogin={setSession}/>
}
