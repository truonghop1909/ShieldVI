import React,{useEffect,useRef,useState} from 'react'
import {saveBlob} from '../../shared/download-file.mjs'
import {liveRequest} from '../../shared/live-transport.mjs'

const sample={thread_id:'ADMIN_JSON_DEMO',profile:'conservative',comments:[
 {comment_id:'c01',user_id:'U01',parent_id:null,timestamp:'2026-11-05T01:00:00Z',text:'Mình chia sẻ lịch sinh hoạt câu lạc bộ, mọi người góp ý nhé.'},
 {comment_id:'c02',user_id:'U02',parent_id:'c01',timestamp:'2026-11-05T01:01:00Z',text:'Mình tham gia được, cảm ơn bạn đã sắp xếp.'},
 {comment_id:'c03',user_id:'U02',parent_id:'c01',timestamp:'2026-11-05T01:02:00Z',text:'Mày là đồ ngu, đừng nói nữa.'},
 {comment_id:'c04',user_id:'U03',parent_id:'c03',timestamp:'2026-11-05T01:03:00Z',text:'Bạn đừng xúc phạm người khác, góp ý lịch thôi nhé.'},
 {comment_id:'c05',user_id:'U02',parent_id:'c01',timestamp:'2026-11-05T01:04:00Z',text:'Mày thật vô dụng, im đi.'}
]}
const statusText={QUEUED:'Đang chờ',RUNNING:'Đang phân tích',COMPLETED:'Hoàn tất',FAILED:'Phân tích thất bại',CANCELLING:'Đang dừng',CANCELLED:'Đã hủy'}
const active=job=>['QUEUED','RUNNING','CANCELLING'].includes(job?.status)

export default function QuickAiTest({session,onExpired}){
 const [text,setText]=useState(''),[job,setJob]=useState(null),[error,setError]=useState(''),[sending,setSending]=useState(false)
 const scope=useRef(null),jobScope=useRef(null)
 useEffect(()=>{const controller=new AbortController();scope.current=controller;return()=>controller.abort()},[session.token])
 useEffect(()=>{if(!job?.id)return;const controller=new AbortController();jobScope.current=controller;let timer
  async function poll(){try{const next=await liveRequest('/moderator/test-conversations/'+job.id,session.token,{signal:controller.signal});if(controller.signal.aborted)return;setJob(next);if(next.status==='FAILED')setError('AI chưa hoàn tất: '+next.error);if(active(next))timer=setTimeout(poll,500)}catch(e){if(controller.signal.aborted)return;if(e.status===401)onExpired();setError(e.status===404?'Phiên test không còn trong bộ nhớ. Hãy chạy lại.':e.message)}}
  poll();return()=>{controller.abort();clearTimeout(timer)}
 },[job?.id,session.token,onExpired])
 async function run(event){event.preventDefault();if(sending||active(job))return;setError('');jobScope.current?.abort();setJob(null);let payload
  try{payload=JSON.parse(text)}catch{setError('JSON không hợp lệ. Kiểm tra dấu ngoặc và dấu phẩy.');return}
  if(new Blob([text]).size>131072){setError('JSON tối đa 128 KiB.');return}
  setSending(true)
  try{const next=await liveRequest('/moderator/test-conversations',session.token,{method:'POST',body:payload,signal:scope.current.signal});setJob(next)}catch(e){if(scope.current.signal.aborted)return;if(e.status===401)onExpired();setError(e.status===404?'Backend chưa nạp mục test JSON. Hãy khởi động lại demo.':e.status===422?'Dữ liệu chưa đúng: cần thread_id, comments (1–50), ID không trùng, parent có trước reply, timestamp có múi giờ và đúng thứ tự.':e.message)}finally{setSending(false)}
 }
 async function importFile(event){const file=event.target.files?.[0];if(!file)return
  if(file.size>131072){setError('File JSON tối đa 128 KiB.');event.target.value='';return}
  try{const value=await file.text();setText(value);setError('')}catch{setError('Không đọc được file JSON.')}finally{event.target.value=''}
 }
 async function cancel(){try{setJob(await liveRequest('/moderator/test-conversations/'+job.id,session.token,{method:'DELETE',signal:scope.current.signal}))}catch(e){setError(e.message)}}
 function download(){saveBlob(new Blob([JSON.stringify(job.result,null,2)],{type:'application/json;charset=utf-8'}),job.result.thread_id.replace(/[^A-Za-z0-9_-]/g,'_')+'_analysis.json')}
 const result=job?.status==='COMPLETED'?job.result:null
 return <div className="quick-ai"><header><div><h1>Test AI bằng JSON</h1><p>Dán hội thoại để phân tích nhanh, không cần đăng bài.</p></div><span>{session.user.username}</span></header>
  <div className="quick-ai-grid"><section className="quick-ai-input"><h2>Hội thoại đầu vào</h2><p className="muted">Tối đa 50 bình luận, 128 KiB. Dùng parent_id để biểu diễn trả lời; timestamp cần có múi giờ.</p>
   <div className="quick-ai-tools"><button type="button" disabled={active(job)||sending} onClick={()=>{setText(JSON.stringify(sample,null,2));setError('')}}>Nạp JSON mẫu</button><label>Nhập file JSON<input type="file" accept=".json,application/json" disabled={active(job)||sending} onChange={importFile}/></label></div>
   <form onSubmit={run}><label htmlFor="quick-json">JSON hội thoại</label><textarea id="quick-json" spellCheck={false} value={text} onChange={e=>setText(e.target.value)} placeholder={'{"thread_id":"test_01","comments":[...]}'} disabled={active(job)||sending}/><div className="quick-ai-tools"><button className="primary" disabled={!text.trim()||active(job)||sending}>{sending?'Đang gửi…':'Phân tích hội thoại'}</button>{active(job)&&<button type="button" onClick={cancel}>Hủy phân tích</button>}</div></form>
   <p className="muted">Kết quả chỉ phục vụ kiểm thử, không phải nhãn người duyệt. Dữ liệu test không được đăng lên Social hay đưa vào huấn luyện.</p>
  </section><section className="quick-ai-results" aria-label="Kết quả test JSON"><h2>Kết quả phân tích</h2>{error&&<p role="alert">{error}</p>}
   {job&&<p role="status" data-testid="quick-test-status">{statusText[job.status]} · {job.completed}/{job.total} bình luận</p>}
   {!job&&!error&&<p className="muted">Dán JSON hoặc nạp mẫu, sau đó bấm Phân tích hội thoại.</p>}
   {result&&<><div className="quick-ai-summary"><strong>{result.comments.length} bình luận · {result.repeated_events.length} cặp repeated</strong><span>{result.model_version} · ngưỡng {result.threshold} · {result.processor}</span><button onClick={download}>Tải kết quả JSON</button></div><div className="quick-ai-table responsive-table"><table><thead><tr><th>Bình luận</th><th>Điểm gốc</th><th>Assessment</th><th>Trả lời</th><th>Target công kích</th><th>Chi tiết</th></tr></thead><tbody>{result.comments.map(row=>{const a=row.analysis,c=a.conversation_signals.current;return <tr key={row.comment_id} data-quick-comment={row.comment_id}><td data-label="Bình luận"><strong>{row.comment_id} · {row.user_id}</strong><p>{row.text}</p></td><td data-label="Điểm gốc">{(a.toxicity_score*100).toFixed(1)}%<small>{a.ai_label}</small></td><td data-label="Assessment">{c.assessment_label}<small>Policy: {c.policy_risk}</small></td><td data-label="Trả lời">{c.reply_to_user_id||'—'}</td><td data-label="Target công kích">{c.directed_at_user_id||'—'}<small>Instance: {String(c.attack_instance_candidate)}</small></td><td data-label="Chi tiết"><details><summary>Context / lexicon</summary><pre>{JSON.stringify({context:c,lexicon:a.lexical_signals,target:a.target_evidence,versions:a.conversation_signals.rules_version},null,2)}</pre></details></td></tr>})}</tbody></table></div><h3>Repeated và bằng chứng</h3>{result.repeated_events.length?result.repeated_events.map((event,index)=><article key={index}><strong>{event.actor_user_id} → {event.target_user_id}</strong><p>{event.evidence_comment_ids.join(', ')}</p></article>):<p>Chưa có bằng chứng repeated đủ điều kiện.</p>}</>}
  </section></div>
 </div>
}
