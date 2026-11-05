import React,{useEffect,useRef,useState} from 'react'
import {RefreshCw} from 'lucide-react'
import {versions} from './api.js'
import {ErrorBox,Pager,fmt,label} from './App.jsx'

function Audit({api,endpoint,version}){
  const [data,setData]=useState(null),[page,setPage]=useState(1),[error,setError]=useState('')
  useEffect(()=>{const c=new AbortController();setData(null);setError('');api(`${endpoint}/audit?page=${page}`,{signal:c.signal}).then(setData).catch(e=>{if(e.name!=='AbortError')setError(e.message)});return()=>c.abort()},[api,endpoint,page,version])
  return <section className="audit"><h3>Lịch sử audit</h3><ErrorBox error={error}/>{!data&&!error&&<p role="status">Đang tải lịch sử…</p>}{data?.items.map(item=><article key={item.id}><strong>{item.event}</strong><time>{fmt(item.created_at)}</time><p>{item.reason}</p><small>{item.actor_type} · {item.actor_id||item.actor_identifier||'system'} · {item.actor_role}<br/>Revision {item.content_revision} · Quyết định {item.decision_version}<br/>{item.before_visibility||'—'} → {item.after_visibility} · {item.policy_version||'Chưa có policy'}</small>{item.details&&<details><summary>Metadata quyết định</summary><pre>{JSON.stringify(item.details,null,2)}</pre></details>}</article>)}<Pager data={data} setPage={setPage}/></section>
}

export default function ReviewDetail({api,selected,user,onMutate}){
  const endpoint=`/moderation/content/${selected.entity_type}/${selected.content.id}`
  const [data,setData]=useState(null),[version,refresh]=useState(0),[reason,setReason]=useState(''),[fp,setFp]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState(false)
  const pending=useRef(null)
  useEffect(()=>()=>pending.current?.abort(),[])
  useEffect(()=>{const c=new AbortController();setData(null);setError('');api(endpoint,{signal:c.signal}).then(setData).catch(e=>{if(e.name!=='AbortError')setError(e.message)});return()=>c.abort()},[api,endpoint,version])
  async function act(action,appeal){
    if(busy||!reason.trim()||!data)return
    const c=new AbortController();pending.current=c;setBusy(true);setError('')
    const row=data.content,path=appeal?`/moderation/appeals/${appeal.id}/resolve`:action==='claim'?`${endpoint}/claim`:action==='retry'?`/moderation/jobs/${data.job.id}/retry`:'/moderation/decisions'
    const body={...versions(row),reason,...(appeal?{outcome:action}:action==='claim'||action==='retry'?{}:{entity_type:selected.entity_type,entity_id:row.id,action,false_positive:fp})}
    try{await api(path,{method:'POST',body,signal:c.signal});if(!c.signal.aborted){setReason('');setFp(false);refresh(v=>v+1);onMutate()}}
    catch(e){if(e.name!=='AbortError')setError(e.message)}finally{if(!c.signal.aborted)setBusy(false)}
  }
  const row=data?.content,ai=data?.ai,appeal=data?.appeals.find(item=>item.status==='OPEN'),deleted=row?.visibility_status==='DELETED_BY_AUTHOR',held=['HIDDEN','HELD_FOR_REVIEW'].includes(row?.visibility_status)
  const disabled=busy||!reason.trim()||Boolean(data?.claim&&data.claim.reviewer_id!==user.id)
  return <section className="review-detail" aria-label="Chi tiết kiểm duyệt"><div className="section-title"><h2>Đọc trước khi quyết định</h2><button aria-label="Tải lại chi tiết" disabled={busy} onClick={()=>refresh(v=>v+1)}><RefreshCw size={16}/></button></div><ErrorBox error={error}/>{!data&&!error&&<p role="status">Đang tải chi tiết…</p>}{data&&<>
    <div className="content-meta"><span>{selected.entity_type==='post'?'BÀI VIẾT':'BÌNH LUẬN'}</span><span>Revision {row.content_revision} · Quyết định {row.decision_version}</span></div><p className="full-text">{row.body??'Tác giả đã xóa nội dung.'}</p>
    <dl className="states"><div><dt>AI label / score</dt><dd>{ai?`${ai.ai_label} / ${ai.toxicity_score.toFixed(4)}`:'Chưa có kết quả AI'}</dd></div><div><dt>Policy risk</dt><dd>{row.risk_tier}</dd></div><div><dt>Visibility</dt><dd>{label(row.visibility_status)}</dd></div><div><dt>Review</dt><dd>{row.review_status}</dd></div></dl>
    <div className="context"><h3>Ngữ cảnh cha</h3>{data.parent_context.length===0?<p className="muted">Không có nội dung cha.</p>:data.parent_context.map(item=><blockquote key={item.id}><small>{item.entity_type} · {label(item.visibility_status)}</small><p>{item.body??'Tác giả đã xóa.'}</p></blockquote>)}</div>
    <details className="evidence" open><summary>Bằng chứng & provenance AI</summary>{ai?<><p><strong>{ai.model_name}</strong><br/>Model: {ai.model_version}<br/>Lexicon: {ai.lexicon_version}<br/>Ngưỡng nhãn: {ai.model_threshold} · {fmt(ai.analyzed_at)}</p><p>Target: {ai.target_evidence.target_user_id||'Chưa xác định'} · {ai.target_evidence.method}</p><p>{ai.suspected_repeated_harassment?'Có candidate công kích lặp lại, cần xác minh.':'Chưa có candidate công kích lặp lại.'}</p><details><summary>Tín hiệu đầy đủ</summary><pre>{JSON.stringify({lexical_signals:ai.lexical_signals,target_evidence:ai.target_evidence,evidence:ai.evidence,limitations:ai.limitations},null,2)}</pre></details></>:<p>Chưa có kết quả AI cho revision này. Có thể duyệt thủ công khi AI offline.</p>}<small>Policy: {data.policy_version||'Chưa áp dụng'} · Job: {data.job?.status||'Không có'}{data.job?.last_error?` · ${data.job.last_error}`:''}</small></details>
    {data.reports.length>0&&<section><h3>Báo cáo người dùng</h3>{data.reports.map(item=><blockquote key={item.id}><p>{item.reason}</p><small>{item.status} · {fmt(item.created_at)}</small></blockquote>)}</section>}
    {data.appeals.length>0&&<section className="appeal"><h3>Kháng nghị</h3>{data.appeals.map(item=><article key={item.id}><p>{item.reason}</p><small>{item.status} · {item.outcome||'Chờ quyết định'} · {fmt(item.created_at)}</small>{item.resolution_reason&&<p>Kết quả: {item.resolution_reason}</p>}</article>)}</section>}
    {!deleted&&<section className="decision"><h3>{appeal?'Quyết định kháng nghị':'Quyết định kiểm duyệt'}</h3>{data.claim&&<p className="muted">Người đang nhận duyệt: {data.claim.reviewer_id} · đến {fmt(data.claim.lease_until)}</p>}<label>Lý do quyết định<textarea rows={3} maxLength={500} value={reason} onChange={e=>setReason(e.target.value)} disabled={busy}/></label>{!appeal&&<label className="check"><input type="checkbox" checked={fp} onChange={e=>setFp(e.target.checked)} disabled={busy}/>Ghi nhận cảnh báo nhầm (feedback, chưa phải nhãn gold)</label>}<div className="decision-buttons">{appeal?<><button className="primary" disabled={disabled} onClick={()=>act('RESTORED',appeal)}>Chấp nhận · khôi phục</button><button disabled={disabled} onClick={()=>act('UPHELD',appeal)}>Giữ quyết định ẩn</button></>:<><button className="primary" disabled={disabled} onClick={()=>act(held?'restore':'approve')}>{held?'Khôi phục':'Cho phép đăng'}</button><button className="danger" disabled={disabled||fp} onClick={()=>act('hide')}>Ẩn nội dung</button></>}{['QUEUED','APPEALED','UNDER_REVIEW'].includes(row.review_status)&&<button disabled={disabled} onClick={()=>act('claim')}>Nhận duyệt 5 phút</button>}{data.job?.status==='FAILED_PERMANENTLY'&&row.visibility_status==='PENDING_MODERATION'&&<button disabled={disabled} onClick={()=>act('retry')}>Thử lại AI</button>}</div>{busy&&<p role="status">Đang lưu…</p>}</section>}
    <Audit api={api} endpoint={endpoint} version={version}/>
  </>}</section>
}
