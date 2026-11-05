import React,{useEffect,useRef,useState} from 'react'
import {ErrorNotice,Loading,PageControls,Status} from './components.jsx'

export function ReportForm({api,row,kind}){
  const [reason,setReason]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[done,setDone]=useState(false)
  const pending=useRef(null)
  useEffect(()=>()=>pending.current?.abort(),[])
  async function submit(e){e.preventDefault();if(busy||!reason.trim())return;const c=new AbortController();pending.current=c;setBusy(true);setError('');try{await api.report(kind==='comments'?'comment':'post',row,reason,c.signal);if(!c.signal.aborted){setDone(true);setReason('')}}catch(e){if(e.name!=='AbortError')setError(e.message)}finally{if(!c.signal.aborted)setBusy(false)}}
  return <details className="user-report"><summary>Báo cáo nội dung</summary>{done?<p role="status">Đã nhận báo cáo. Nội dung sẽ được xem xét, không tự ẩn do số báo cáo.</p>:<form onSubmit={submit}><label>Lý do báo cáo<textarea required maxLength={500} value={reason} onChange={e=>setReason(e.target.value)} disabled={busy}/></label><ErrorNotice message={error}/><button className="button quiet" disabled={busy||!reason.trim()}>Gửi báo cáo</button></form>}</details>
}

function Item({item,api,onChange}){
  const [reason,setReason]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('')
  const pending=useRef(null)
  useEffect(()=>()=>pending.current?.abort(),[])
  async function submit(e){e.preventDefault();if(busy||!reason.trim())return;const c=new AbortController();pending.current=c;setBusy(true);setError('');try{await api.appeal(item.entity_type,item.content,reason,c.signal);if(!c.signal.aborted)onChange()}catch(e){if(e.name!=='AbortError')setError(e.message)}finally{if(!c.signal.aborted)setBusy(false)}}
  return <article className="card moderation-item" aria-label="Nội dung của tôi"><small>{item.entity_type==='post'?'Bài viết':'Bình luận'} · Revision {item.content.content_revision}</small><p className="content-body">{item.content.body}</p><Status row={item.content}/>{item.decision_reason&&<p>Lý do quyết định: {item.decision_reason}</p>}{item.appeals.map(appeal=><div key={appeal.id} className="appeal-result"><strong>Kháng nghị: {appeal.status==='OPEN'?'Đang chờ xem xét':appeal.outcome==='RESTORED'?'Đã được khôi phục':appeal.outcome==='UPHELD'?'Giữ quyết định ẩn':appeal.outcome==='SUPERSEDED'?'Đã thay bằng phiên bản mới':appeal.status}</strong><p>{appeal.reason}</p>{appeal.resolution_reason&&<p>Phản hồi: {appeal.resolution_reason}</p>}</div>)}{item.can_appeal&&<form onSubmit={submit}><label>Lý do kháng nghị<textarea required rows={3} maxLength={500} value={reason} onChange={e=>setReason(e.target.value)} disabled={busy}/></label><ErrorNotice message={error}/><button className="button primary" disabled={busy||!reason.trim()}>Gửi kháng nghị</button><small>Nội dung giữ trạng thái hiện tại trong lúc chờ người kiểm duyệt.</small></form>}</article>
}

export default function MyModeration({api}){
  const [data,setData]=useState(null),[page,setPage]=useState(1),[version,refresh]=useState(0),[error,setError]=useState('')
  useEffect(()=>{const c=new AbortController();setData(null);setError('');api.myModeration(page,c.signal).then(setData).catch(e=>{if(e.name!=='AbortError')setError(e.message)});return()=>c.abort()},[api,page,version])
  return <><div className="page-heading"><div><p className="eyebrow">GÓC CỦA BẠN</p><h1>Nội dung & kháng nghị</h1><p className="muted">Xem trạng thái thật và gửi lời giải thích khi nội dung bị ẩn hoặc giữ.</p></div><button className="button quiet" onClick={()=>refresh(v=>v+1)}>Làm mới trạng thái</button></div><ErrorNotice message={error}/>{!data&&!error&&<Loading/>}{data?.items.length===0&&<p>Bạn chưa có nội dung.</p>}{data?.items.map(item=><Item key={`${item.entity_type}:${item.content.id}:${item.content.content_revision}:${item.content.decision_version}`} item={item} api={api} onChange={()=>refresh(v=>v+1)}/>)}<PageControls data={data} change={setPage} busy={!data}/></>
}
