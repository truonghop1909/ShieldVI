import React, { useEffect, useRef, useState } from 'react'
import {
  Activity, AlertCircle, AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight,
  BarChart3, Check, CheckCircle2, ChevronDown, CircleHelp, Clock3, Database,
  Download, FileJson2, FileText, GitBranch, Info, LayoutDashboard, Loader2,
  Menu, MessageCircle, MessageSquareMore, Plus, RefreshCcw, Search, Send,
  Settings2, Shield, ShieldAlert, ShieldCheck, SlidersHorizontal, Sparkles,
  Trash2, Upload, Users, X
} from 'lucide-react'
import {
  SAMPLE_THREAD, makeEditable, nowLocalInput, requestFromEditor,
  validateInput, downloadBlob, exportCsv, friendlyError
} from './utils.js'

const STATUS = {
  suspected_repeated: {title: 'Nghi công kích lặp lại', tone: 'red', note: 'Cần người kiểm duyệt xem xét các bằng chứng'},
  needs_review: {title: 'Cần xem xét', tone: 'amber', note: 'Có tín hiệu nhạy cảm, cần xác nhận thủ công'},
  none: {title: 'Chưa có cảnh báo lặp lại', tone: 'green', note: 'Không phát hiện đủ bằng chứng theo quy tắc đang dùng'}
}

const LEXICAL_CATEGORIES = {
  profanity: 'Chửi tục', directed_insult: 'Công kích tiềm năng',
  ambiguous: 'Mơ hồ / đa nghĩa', other_sensitive: 'Nhạy cảm theo ngữ cảnh',
  vi_profanity: 'Chửi tục', en_profanity: 'Chửi tục',
  direct_insult: 'Công kích tiềm năng', ambiguous_slang: 'Mơ hồ / đa nghĩa'
}

function PanelTitle({icon: Icon, title, subtitle, end}) {
  return <div className="panel-heading">
    <div className="panel-heading-left"><div className="panel-icon"><Icon size={18}/></div>
      <div><h3>{title}</h3>{subtitle && <p>{subtitle}</p>}</div>
    </div>
    {end && <div className="heading-actions">{end}</div>}
  </div>
}

function IconButton({icon: Icon, title, onClick, disabled=false}) {
  return <button type="button" className="icon-btn" onClick={onClick} disabled={disabled} aria-label={title} title={title}><Icon size={17}/></button>
}

function MetricCard({icon: Icon, label, value, sub, tone='neutral'}) {
  return <div className={`metric-card metric-${tone}`}>
    <div className="metric-top"><span>{label}</span><span className="metric-icon"><Icon size={19}/></span></div>
    <div className="metric-value">{value}</div>
    <div className="metric-sub">{sub}</div>
  </div>
}

function HeaderStatus({health, loading, onRetry}) {
  const online = health?.model_loaded === true
  const hasError = health && !online
  return <button type="button" className={`server-status ${online?'connected':hasError?'disconnected':''}`} onClick={onRetry} title="Nhấn để kiểm tra lại kết nối">
    {loading ? <Loader2 size={15} className="spin"/> : <span className="status-led"/>}
    <span>{loading?'Đang kiểm tra':online?'Mô hình đã sẵn sàng':hasError?'Chưa tải được ViSoBERT':'Đang kết nối'}</span>
    <RefreshCcw size={13}/>
  </button>
}

function RiskGauge({result}) {
  const risk = result ? Math.max(0,Math.min(100,result.risk_score_heuristic || 0)) : 0
  const status = STATUS[result?.risk_level] || STATUS.none
  const circumference = 2 * Math.PI * 54
  return <div className={`risk-card ${result ? 'has-result' : ''}`}>
    <div className="risk-heading"><div><p className="eyebrow">TỔNG HỢP RỦI RO</p><h3>Đánh giá hội thoại</h3></div><ShieldAlert size={22}/></div>
    <div className="gauge-layout">
      <div className="gauge-holder">
        <svg viewBox="0 0 152 152" role="img" aria-label={`Điểm rủi ro quy tắc: ${risk} trên 100`}>
          <circle cx="76" cy="76" r="54" fill="none" stroke="rgba(255,255,255,.12)" strokeWidth="12"/>
          <circle cx="76" cy="76" r="54" fill="none" stroke="#5aefcf" strokeWidth="12" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference * (1-risk/100)} transform="rotate(-90 76 76)" style={{transition:'stroke-dashoffset .6s'}}/>
        </svg>
        <div className="gauge-center"><strong>{result ? risk : '—'}</strong><span>điểm / 100</span></div>
      </div>
      <div className="gauge-description"><span className={`risk-label ${result ? status.tone : ''}`}>{result ? status.title : 'Chưa phân tích'}</span><p>{result ? status.note : 'Nhập hội thoại rồi nhấn Phân tích để xem cảnh báo và bằng chứng.'}</p></div>
    </div>
    <div className="risk-foot"><Info size={15}/><span>Điểm rủi ro theo quy tắc (heuristic), không phải xác suất đã hiệu chuẩn.</span></div>
  </div>
}

function ThreadEditor({threadId,setThreadId,profile,setProfile,rows,setRows,onAnalyze,busy,onSample,onImport,onExport}) {
  const [showOptions,setShowOptions] = useState(false)
  const update = (index, key, val) => setRows(previous=>previous.map((c,i)=>i===index?{...c,[key]:val}:c))
  const add = () => {
    const idSeed = rows.length+1
    let id = `c${idSeed}`
    while (rows.some(x=>x.comment_id===id)) id = `c${Math.floor(Math.random()*100000)}`
    setRows(previous=>[...previous,{
      comment_id:id,user_id:'U01',text:'',parent_id:previous[previous.length-1]?.comment_id || '',timestamp:nowLocalInput(),mentioned_user_ids:''
    }])
  }
  return <section className="panel editor-panel" id="thread-editor">
    <PanelTitle icon={MessageSquareMore} title="Dữ liệu hội thoại" subtitle="Chỉnh sửa từng bình luận hoặc nhập file JSON"
      end={<div className="toolbar"><button className="text-btn" type="button" onClick={onSample}><RefreshCcw size={14}/> Nạp mẫu</button><button className="text-btn" type="button" onClick={onImport}><Upload size={14}/> Nhập JSON</button><IconButton icon={Download} title="Tải hội thoại JSON" onClick={onExport}/></div>} />
    <div className="editor-controls">
      <div className="field"><label htmlFor="thread-id">Mã hội thoại</label><input id="thread-id" value={threadId} onChange={e=>setThreadId(e.target.value)} placeholder="VD: THREAD_001" maxLength="120"/></div>
      <div className="field"><label htmlFor="profile">Chế độ phân tích</label><select id="profile" value={profile} onChange={e=>setProfile(e.target.value)}><option value="conservative">Kiểm duyệt — ngưỡng 0.41</option><option value="research_synthetic">Nghiên cứu mô phỏng — 0.03</option></select></div>
    </div>
    {profile==='research_synthetic' && <div className="inline-warning"><AlertTriangle size={15}/> Chế độ 0.03 chỉ dành cho dữ liệu mô phỏng; không dùng kết quả để quyết định xử phạt.</div>}
    <div className="comments-editor-scroll"><div className="comments-editor">
      {rows.map((c,index)=><div className="comment-edit" key={`${index}-${c.comment_id}`}>
        <div className="comment-number"><span>{String(index+1).padStart(2,'0')}</span><span className="reply-line"/></div>
        <div className="comment-edit-body">
          <div className="comment-edit-top"><div className="tiny-fields">
            <label>ID<input aria-label={`Mã bình luận ${index+1}`} value={c.comment_id} onChange={e=>update(index,'comment_id',e.target.value)}/></label>
            <label>Người gửi<input aria-label={`Người gửi ${index+1}`} value={c.user_id} onChange={e=>update(index,'user_id',e.target.value)}/></label>
            <label>Trả lời ID<input aria-label={`Trả lời ${index+1}`} value={c.parent_id} placeholder="—" onChange={e=>update(index,'parent_id',e.target.value)}/></label>
            <label>Thời gian<input aria-label={`Thời gian ${index+1}`} value={c.timestamp} type="datetime-local" onChange={e=>update(index,'timestamp',e.target.value)}/></label>
          </div><IconButton icon={Trash2} title="Xóa bình luận" onClick={()=>setRows(r=>r.filter((_,i)=>i!==index))} disabled={rows.length===1}/></div>
          <textarea aria-label={`Nội dung bình luận ${index+1}`} placeholder="Nhập nội dung bình luận tiếng Việt..." rows="2" value={c.text} maxLength={8000} onChange={e=>update(index,'text',e.target.value)}/>
          {showOptions && <div className="mention-field"><label>ID được nhắc tới (nếu nền tảng cung cấp)</label><input value={c.mentioned_user_ids} onChange={e=>update(index,'mentioned_user_ids',e.target.value)} placeholder="VD: U01, U03"/></div>}
        </div>
      </div>)}
    </div></div>
    <div className="editor-footer"><div className="footer-tools"><button className="secondary-btn" type="button" onClick={add}><Plus size={15}/> Thêm bình luận</button><button className="show-options" onClick={()=>setShowOptions(v=>!v)} type="button"><SlidersHorizontal size={15}/>{showOptions?'Ẩn':'Thêm'} thông tin mention</button></div><button className="primary-btn" disabled={busy} onClick={onAnalyze} type="button">{busy?<Loader2 size={17} className="spin"/>:<Sparkles size={17}/>} {busy?'Đang phân tích...':'Phân tích hội thoại'} <ArrowRight size={16}/></button></div>
  </section>
}

function EvidencePanel({result}) {
  const evidence = result?.evidence || []
  return <section className="panel evidence-panel">
    <PanelTitle icon={ShieldCheck} title="Bằng chứng & cảnh báo" subtitle="Các chuỗi công kích nghi vấn do quy tắc tìm thấy" end={result&&<span className="small-count">{evidence.length} chuỗi</span>}/>
    {!result ? <div className="placeholder"><div className="placeholder-icon"><GitBranch size={24}/></div><strong>Chưa có bằng chứng</strong><p>Chạy phân tích để xem các lượt công kích đáng kiểm tra.</p></div> : evidence.length===0 ? <div className="placeholder compact"><ShieldCheck size={26}/><strong>Chưa phát hiện chuỗi lặp lại</strong><p>Không có nghĩa mọi bình luận đều an toàn.</p></div>:
      <div className="evidence-list">{evidence.map((item,index)=><div className="evidence-item" key={`${index}-${item.actor_user_id}`}><div className="evidence-pair"><span className="person-chip actor">{item.actor_user_id}</span><ArrowRight size={16}/><span className="person-chip target">{item.target_user_id}</span></div><div className="evidence-meta"><span><MessageCircle size={13}/> {item.evidence_comment_ids.length} bình luận</span><span><Clock3 size={13}/> {item.n_distinct_timestamps} thời điểm</span></div><div className="evidence-ids">Bằng chứng: <strong>{item.evidence_comment_ids.join(', ')}</strong></div></div>)}</div>
    }
  </section>
}

function ResultsTable({result,rows,onExportCsv,onExportJson,reviewLabels,onReview,onExportReviews,reviewerId,setReviewerId,onSaveReviews,onLoadReviews,savingReviews,reviewStatus}) {
  const [filter,setFilter] = useState('all')
  const [query,setQuery] = useState('')
  const [collapsedComments,setCollapsedComments] = useState(() => new Set())
  useEffect(() => { setCollapsedComments(new Set()) }, [result])
  const data = result?.comments || []
  const inputLookup = Object.fromEntries(rows.map(c=>[c.comment_id,c]))
  const commentText = c => c.text ?? inputLookup[c.comment_id]?.text ?? '(nội dung không có trong bộ nhập hiện tại)'
  const isLongComment = c => commentText(c).length > 280 || commentText(c).split(/\r\n|\r|\n/).length > 4
  const longComments = data.filter(isLongComment)
  const toggleComment = id => setCollapsedComments(current => {
    const next = new Set(current)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    return next
  })
  const reviewedCount = data.filter(c => reviewLabels[c.comment_id]).length
  const shown = data.filter(c => (filter==='all'||(filter==='toxic'&&c.toxic_for_moderation)||(filter==='lexical'&&(c.lexical_signals||[]).length>0)||(filter==='safe'&&!c.toxic_for_moderation)) && (`${c.comment_id} ${c.user_id} ${commentText(c)}`.toLowerCase().includes(query.toLowerCase())))
  return <section className="panel table-panel" id="comment-results">
    <PanelTitle icon={BarChart3} title="Kết quả từng bình luận" subtitle={`Điểm toxicity từ ${result?.model_name || 'ViSoBERT'}`} end={result && <div className="toolbar"><button className="text-btn" type="button" onClick={onExportCsv}><Download size={14}/> CSV AI</button><button className="text-btn" type="button" onClick={onExportJson}><Download size={14}/> JSON AI</button></div>}/>
    {result && <div className="table-toolbar"><div className="filter-pills"><button className={filter==='all'?'active':''} onClick={()=>setFilter('all')}>Tất cả <span>{data.length}</span></button><button className={filter==='toxic'?'active':''} onClick={()=>setFilter('toxic')}>Nghi toxic <span>{data.filter(x=>x.toxic_for_moderation).length}</span></button><button className={filter==='lexical'?'active':''} onClick={()=>setFilter('lexical')}>Từ lóng / tục <span>{data.filter(x=>(x.lexical_signals||[]).length>0).length}</span></button><button className={filter==='safe'?'active':''} onClick={()=>setFilter('safe')}>Không cảnh báo <span>{data.filter(x=>!x.toxic_for_moderation).length}</span></button></div><div className="search"><Search size={15}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Tìm bình luận..."/></div></div>}
    {result && <div className="comment-display-toolbar">
      <span>Bình luận hiển thị đầy đủ mặc định · Có thể cuộn ngang để xem các cột</span>
      <div className="toolbar" role="group" aria-label="Hiển thị nội dung bình luận">
        <button className="secondary-btn" type="button" disabled={!longComments.some(c=>collapsedComments.has(c.comment_id))} onClick={()=>setCollapsedComments(new Set())}>Mở rộng tất cả</button>
        <button className="secondary-btn" type="button" disabled={!longComments.some(c=>!collapsedComments.has(c.comment_id))} onClick={()=>setCollapsedComments(new Set(longComments.map(c=>c.comment_id)))}>Thu gọn tất cả</button>
      </div>
    </div>}
    {result && <div className="review-toolbar">
      <div className="review-toolbar-copy"><strong><ShieldCheck size={16}/> Xác nhận nhãn bởi người kiểm duyệt</strong><span>{reviewedCount}/{data.length} bình luận đã được gán nhãn thủ công. Kết quả này không thay đổi dự đoán hay cảnh báo AI.</span></div>
      <label className="reviewer-label">Người đánh giá <input aria-label="Mã người đánh giá" value={reviewerId} onChange={e=>setReviewerId(e.target.value)} placeholder="A" maxLength={30}/></label>
      <button className="secondary-btn" type="button" disabled={!result || savingReviews || !reviewerId.trim()} onClick={onLoadReviews}><RefreshCcw size={15}/> Tải nhãn đã lưu</button>
      <button className="secondary-btn" type="button" disabled={reviewedCount===0 || !reviewerId.trim() || savingReviews} onClick={onSaveReviews}><Database size={15}/> {savingReviews?'Đang lưu...':'Lưu vào SQLite'}</button>
      <button className="secondary-btn" type="button" disabled={reviewedCount===0 || !reviewerId.trim()} onClick={onExportReviews}><Download size={15}/> Xuất nhãn CSV</button>
      {reviewStatus && <span className="review-status" role="status">{reviewStatus}</span>}
    </div>}
    {!result ? <div className="placeholder table-empty"><MessageCircle size={26}/><strong>Đang chờ dữ liệu phân tích</strong><p>Danh sách điểm toxic và mục tiêu sẽ hiển thị ở đây.</p></div>:
    <div className="table-scroll" role="region" aria-label="Bảng kết quả bình luận, có thể cuộn ngang" tabIndex={0}><table><colgroup><col className="comment-column"/><col className="score-column"/><col className="ai-column"/><col className="lexical-column"/><col className="target-column"/><col className="confidence-column"/><col className="review-column"/></colgroup><thead><tr><th>Bình luận</th><th>Điểm toxic</th><th>Đánh giá AI</th><th>Từ lóng / tục</th><th>Mục tiêu</th><th>Độ tin cậy</th><th>Xác nhận thủ công</th></tr></thead><tbody>{shown.map(c=>{
      const collapsed = isLongComment(c) && collapsedComments.has(c.comment_id)
      const textId = `result-comment-${c.comment_id}`
      return <tr key={c.comment_id}><td><div className="table-comment"><div className="table-comment-id">{c.comment_id} <span>· {c.user_id}</span></div><p id={textId} className={collapsed ? 'comment-text is-collapsed' : 'comment-text'}>{commentText(c)}</p>
        {isLongComment(c) && <button className="comment-toggle" type="button" aria-expanded={!collapsed} aria-controls={textId} aria-label={`${collapsed ? 'Xem đầy đủ' : 'Thu gọn'} bình luận ${c.comment_id}`} onClick={()=>toggleComment(c.comment_id)}>{collapsed ? 'Xem đầy đủ' : 'Thu gọn'}<ChevronDown size={14} className={collapsed ? '' : 'rotate-up'}/></button>}</div></td><td><div className="score-wrap"><strong>{(c.toxicity_score*100).toFixed(1)}%</strong><div className="score-track"><div className={`score-fill ${c.toxic_for_moderation?'hot':'cool'}`} style={{width:`${Math.max(0,Math.min(100,c.toxicity_score*100))}%`}}/></div></div></td><td><span className={`table-badge ${c.toxic_for_moderation?'toxic':'clear'}`}>{c.toxic_for_moderation?<AlertTriangle size={13}/>:<CheckCircle2 size={13}/>} {c.toxic_for_moderation?'Nghi toxic':'Không cảnh báo'}</span></td><td>{(c.lexical_signals||[]).length>0 ? <div className="lexical-cell"><strong className="lexical-chip">{c.lexical_review_recommended?'Từ ngữ cần rà soát':'Tín hiệu theo ngữ cảnh'}</strong>{c.directed_insult_candidate && <span className="lexical-small">Nghi nhắm tới người</span>}{c.reported_or_apology_context && <span className="lexical-small">Có ngữ cảnh tường thuật/xin lỗi</span>}<ul className="lexical-matches">{(c.lexical_signals||[]).map((signal,index)=><li className={`lexical-match category-${signal.category}`} key={`${signal.rule_id}-${signal.start ?? index}`}>
          <strong className="lexical-match-form">{signal.matched_form}</strong>
          <span>Từ gốc: <b>{signal.canonical_form || signal.matched_form}</b></span>
          <div className="lexical-match-meta"><span>{({vi:'Tiếng Việt',en:'Tiếng Anh'})[signal.language] || 'Chưa rõ ngôn ngữ'}</span><span>{LEXICAL_CATEGORIES[signal.category] || signal.category}</span></div>
          <p>{signal.reason || 'Tín hiệu từ vựng cần kiểm tra ngữ cảnh; không tự gán TOXIC.'}</p>
        </li>)}</ul></div>:<span className="lexical-small">Không thấy từ khóa</span>}</td><td><span className="target-text">{c.target_user_id||'Chưa rõ'}</span></td><td><span className="confidence">{({high:'Cao',medium:'Trung bình',low:'Thấp',none:'Chưa rõ'})[c.target_confidence]||'Chưa rõ'}</span></td><td><select aria-label={`Gán nhãn bình luận ${c.comment_id}`} className={`review-select ${reviewLabels[c.comment_id]||''}`} value={reviewLabels[c.comment_id]||''} onChange={e=>onReview(c.comment_id,e.target.value)}><option value="">Chưa gán</option><option value="clean">CLEAN</option><option value="toxic">TOXIC</option><option value="uncertain">CHƯA CHẮC</option></select></td></tr>
    })}</tbody></table>{shown.length===0&&<div className="no-results">Không tìm thấy bình luận phù hợp bộ lọc.</div>}</div>}
  </section>
}

function NetworkGraph({result,rows}) {
  const users = Array.from(new Set(rows.map(x=>x.user_id))).filter(Boolean).slice(0,8)
  const edges = result?.evidence || []
  const center = {x:340,y:132}
  const radius = users.length<3?126:150
  const points = Object.fromEntries(users.map((u,i)=>{
    const angle = -Math.PI/2 + 2*Math.PI*i/users.length
    return [u,{x:center.x+radius*Math.cos(angle),y:center.y+90*Math.sin(angle)}]
  }))
  const actors = new Set(edges.map(e=>e.actor_user_id))
  const targets = new Set(edges.map(e=>e.target_user_id))
  return <section className="panel graph-panel"><PanelTitle icon={GitBranch} title="Sơ đồ tương tác" subtitle="Mũi tên đỏ biểu diễn chuỗi công kích nghi vấn có bằng chứng"/>
    {!result?<div className="placeholder compact"><Users size={25}/><strong>Sơ đồ sẽ xuất hiện sau phân tích</strong><p>Quan hệ được suy ra từ ID người gửi và bằng chứng.</p></div>:
      <><div className="graph-canvas"><svg viewBox="0 0 680 270" role="img" aria-label="Sơ đồ người gửi và người bị nhắm tới"><defs><marker id="arrowRed" markerWidth="8" markerHeight="8" refX="20" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#e26666" strokeWidth="1.7"/></marker></defs>
        {edges.filter(e=>points[e.actor_user_id]&&points[e.target_user_id]&&e.actor_user_id!==e.target_user_id).map((e,i)=>{
          const a=points[e.actor_user_id],b=points[e.target_user_id]
          return <g key={`${e.actor_user_id}${e.target_user_id}${i}`}><line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#e26666" strokeWidth="3" strokeLinecap="round" markerEnd="url(#arrowRed)" opacity=".9"/><rect x={(a.x+b.x)/2-13} y={(a.y+b.y)/2-12} width="26" height="23" rx="8" fill="#fff" stroke="#f1dadb"/><text x={(a.x+b.x)/2} y={(a.y+b.y)/2+4} textAnchor="middle" fill="#b44848" fontWeight="700" fontSize="12">{e.evidence_comment_ids.length}</text></g>
        })}
        {users.map(u=>{const p=points[u];const isActor=actors.has(u),isTarget=targets.has(u);return <g key={u}><circle cx={p.x} cy={p.y} r="29" fill={isActor?'#fff0f0':isTarget?'#effaf7':'#f5f7fc'} stroke={isActor?'#e08b8b':isTarget?'#6ab9a3':'#cbd5e3'} strokeWidth="2"/><text x={p.x} y={p.y+5} textAnchor="middle" fontSize="13" fontWeight="700" fill={isActor?'#ac4040':isTarget?'#167b66':'#465772'}>{u}</text></g>})}
      </svg></div><div className="graph-legend"><span><i className="legend-dot actor-dot"/> Người bị nghi công kích</span><span><i className="legend-dot target-dot"/> Người bị nhắm tới</span><span><i className="legend-dot neutral-dot"/> Người tham gia</span></div>{edges.length===0&&<p className="graph-note">Chưa có cạnh lặp lại đủ điều kiện cảnh báo. Không đồng nghĩa không có bình luận độc hại.</p>}</>}
  </section>
}

function WarningPanel({result}) {
  return <section className="panel caution-panel"><PanelTitle icon={Info} title="Giải thích & giới hạn" subtitle="Các lưu ý quan trọng khi sử dụng kết quả"/><div className="warning-list">{(result?.warnings || [
    'Hệ thống chỉ hỗ trợ người kiểm duyệt, không tự động kết luận một cá nhân có hành vi bắt nạt.',
    'Kết quả trên dữ liệu mô phỏng chưa chứng minh hiệu năng trên hội thoại thật.',
    'Đầu vào chỉ dùng mã người dùng ẩn danh; không nhập dữ liệu cá nhân nhạy cảm.'
  ]).map((x,i)=><div key={i} className="warning-row"><Info size={15}/><p>{x}</p></div>)}</div></section>
}

function RecentTab({recent,loading,onRefresh}) {
  return <section className="panel history-panel"><PanelTitle icon={Clock3} title="Lịch sử phân tích" subtitle="Metadata gần đây, chỉ có khi backend bật STORE_SUMMARIES=1" end={<button className="secondary-btn" onClick={onRefresh}><RefreshCcw size={15} className={loading?'spin':''}/> Làm mới</button>}/>
  {!recent?.storage_enabled?<div className="placeholder big"><Database size={28}/><strong>Lưu lịch sử đang tắt</strong><p>Đây là cấu hình an toàn mặc định. Nếu cần demo lịch sử, có thể bật STORE_SUMMARIES=1 tại backend. Hệ thống không lưu nguyên văn bình luận.</p></div>:
  <div className="table-scroll"><table><thead><tr><th>Thời điểm</th><th>Hội thoại</th><th>Mức rủi ro</th><th>Chi tiết</th></tr></thead><tbody>{(recent.items||[]).map((x,i)=><tr key={i}><td>{x.created_at||x.timestamp||'—'}</td><td>{x.thread_id||'—'}</td><td>{x.risk_level||'—'}</td><td>{x.suspected_repeated_harassment?'Có nghi vấn':'Chưa cảnh báo'}</td></tr>)}</tbody></table>{!(recent.items||[]).length&&<div className="no-results">Chưa có lịch sử.</div>}</div>}</section>
}

function ReviewStatsTab({stats,onRefresh,busy,onExport}) {
  return <section className="panel history-panel">
    <PanelTitle icon={BarChart3} title="Thống kê kiểm duyệt" subtitle="Chỉ tính các nhãn bạn đã lưu vào SQLite; CHƯA CHẮC không được tính vào FP/FN" end={<div className="toolbar"><button className="secondary-btn" type="button" onClick={onRefresh}><RefreshCcw size={15} className={busy?'spin':''}/> Làm mới</button><button className="secondary-btn" type="button" onClick={onExport}><Download size={15}/> Xuất SQLite CSV</button></div>}/>
    {!stats?<div className="placeholder compact">Chọn Làm mới để tải thống kê nhãn.</div>:
    <><div className="review-stats-grid">{[
      ['Tổng nhãn',stats.total_reviews],['Đã xác nhận',stats.confirmed],
      ['Chưa chắc',stats.uncertain],['Báo nhầm (FP)',stats.false_positive],
      ['Bỏ sót (FN)',stats.false_negative],['Phát hiện đúng (TP)',stats.true_positive]
    ].map(([name,count])=><div className="review-stat" key={name}><small>{name}</small><strong>{count}</strong></div>)}</div>
    <p className="review-caution">{stats.limitation} Bạn làm đồ án một mình nên chưa có đánh giá nhất quán giữa hai annotator.</p></>}
  </section>
}

export default function App() {
  const [active,setActive] = useState('analyze')
  const [mobileMenu,setMobileMenu] = useState(false)
  const [threadId,setThreadId] = useState(SAMPLE_THREAD.thread_id)
  const [profile,setProfile] = useState('conservative')
  const [rows,setRows] = useState(makeEditable(SAMPLE_THREAD.comments))
  const [result,setResult] = useState(null)
  const [reviewLabels,setReviewLabels] = useState({})
  const [savingReviews,setSavingReviews] = useState(false)
  const [reviewStatus,setReviewStatus] = useState('')
  const [reviewStats,setReviewStats] = useState(null)
  const [loadingReviewStats,setLoadingReviewStats] = useState(false)
  const [reviewerId,setReviewerId] = useState('A')
  const [health,setHealth] = useState(null)
  const [checking,setChecking] = useState(true)
  const [busy,setBusy] = useState(false)
  const [error,setError] = useState('')
  const [recent,setRecent] = useState(null)
  const [loadingRecent,setLoadingRecent] = useState(false)
  const importRef = useRef(null)

  async function refreshHealth() {
    setChecking(true)
    try {const r=await fetch('/health');const j=await r.json();setHealth(j);if(!r.ok)throw new Error(`HTTP ${r.status}`)}
    catch(e){setHealth({model_loaded:false,details:e.message})}
    finally{setChecking(false)}
  }
  useEffect(()=>{refreshHealth()},[])

  async function analyze() {
    setError('')
    let payload
    try {payload=requestFromEditor(threadId,profile,rows);validateInput(payload)}
    catch(e){setError(e.message);return}
    setBusy(true)
    try {
      const r=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
      const j=await r.json()
      if(!r.ok) throw new Error(friendlyError(r,j))
      setResult(j)
      setReviewLabels({})
      setReviewStatus('')
      setActive('analyze')
      setTimeout(()=>document.getElementById('comment-results')?.scrollIntoView({behavior:'smooth',block:'nearest'}),250)
    } catch(e){setError(e.message||'Không kết nối được FastAPI. Hãy chạy backend ở cổng 8000.');setResult(null)}
    finally {setBusy(false)}
  }
  function loadSample(){setThreadId(SAMPLE_THREAD.thread_id);setProfile('conservative');setRows(makeEditable(SAMPLE_THREAD.comments));setResult(null);setReviewLabels({});setReviewStatus('');setError('')}
  async function importJson(e){
    const f=e.target.files?.[0];if(!f)return
    try{
      const data=JSON.parse(await f.text());if(!data.thread_id||!Array.isArray(data.comments))throw new Error('JSON phải có thread_id và comments[].')
      const converted=makeEditable(data.comments);validateInput(requestFromEditor(String(data.thread_id),data.profile==='research_synthetic'?'research_synthetic':'conservative',converted))
      setThreadId(String(data.thread_id));setRows(converted);setProfile(data.profile==='research_synthetic'?'research_synthetic':'conservative');setResult(null);setReviewLabels({});setReviewStatus('');setError('')
    }catch(err){setError('Không nhập được JSON: '+err.message)}finally{e.target.value=''}
  }
  function onReview(commentId, label) {
    setReviewLabels(current => {
      const next = {...current}
      if (label) next[commentId] = label
      else delete next[commentId]
      return next
    })
  }
  async function saveReviews(){
    if (!result || !reviewerId.trim()) return
    const items = result.comments.filter(c=>reviewLabels[c.comment_id]).map(c=>({
      comment_id:c.comment_id,human_label:reviewLabels[c.comment_id],
      ai_label:c.toxic_for_moderation?'toxic':'clean',
      toxicity_score:c.toxicity_score,
      lexical_flag:!!c.lexical_review_recommended
    }))
    if (!items.length) {setReviewStatus('Chưa có nhãn để lưu');return}
    setSavingReviews(true)
    try {
      const res=await fetch('/api/reviews/batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({thread_id:result.thread_id,reviewer_id:reviewerId.trim(),items})})
      const data=await res.json()
      if (!res.ok)throw new Error(friendlyError(res,data))
      setReviewStatus(`Đã lưu ${data.saved} nhãn vào SQLite (không lưu nội dung gốc).`)
    }catch(e){setReviewStatus(`Lưu thất bại: ${e.message}`)}
    finally{setSavingReviews(false)}
  }
  async function loadReviews(){
    if (!result || !reviewerId.trim())return
    try{
      const url=`/api/reviews?thread_id=${encodeURIComponent(result.thread_id)}&reviewer_id=${encodeURIComponent(reviewerId.trim())}`
      const res=await fetch(url)
      if(!res.ok)throw new Error(`HTTP ${res.status}`)
      const data=await res.json()
      const allowed=new Set(result.comments.map(c=>c.comment_id))
      const labels=Object.fromEntries((data.items||[]).filter(r=>allowed.has(r.comment_id)).map(r=>[r.comment_id,r.human_label]))
      setReviewLabels(labels)
      setReviewStatus(`Đã tải ${Object.keys(labels).length} nhãn từ SQLite.`)
    }catch(e){setReviewStatus(`Tải thất bại: ${e.message}`)}
  }
  async function refreshReviewStats(){
    setLoadingReviewStats(true)
    try{const r=await fetch('/api/reviews/stats');if(!r.ok)throw new Error(`HTTP ${r.status}`);setReviewStats(await r.json())}
    catch(e){setError(`Không lấy được thống kê: ${e.message}`)}
    finally{setLoadingReviewStats(false)}
  }
  function exportDatabase(){window.open('/api/reviews/export','_blank','noopener,noreferrer')}
  function exportReviews() {
    if (!result || !reviewerId.trim()) return
    const escape = val => '"' + String(val ?? '').replace(/"/g,'""') + '"'
    const header = ['thread_id','comment_id','user_id','reviewer_id','human_label','ai_label','toxicity_score','target_user_id','model_name','profile','labeled_at_utc']
    const now = new Date().toISOString()
    const records = result.comments.filter(c => reviewLabels[c.comment_id]).map(c=>[
      result.thread_id,c.comment_id,c.user_id,reviewerId.trim(),reviewLabels[c.comment_id],
      c.toxic_for_moderation?'toxic':'clean',c.toxicity_score,c.target_user_id||'',
      result.model_name,result.profile,now
    ])
    if (!records.length) return
    const content='\uFEFF' + [header.map(escape).join(','),...records.map(r=>r.map(escape).join(','))].join('\r\n')
    downloadBlob(`${result.thread_id}_review_${reviewerId.trim()}.csv`,content,'text/csv;charset=utf-8')
  }
  function exportInput(){try{const payload=requestFromEditor(threadId,profile,rows);validateInput(payload);downloadBlob(`${threadId||'thread'}_input.json`,JSON.stringify(payload,null,2))}catch(e){setError(e.message)}}
  function exportResult(){if(result)downloadBlob(`${result.thread_id}_analysis.json`,JSON.stringify(result,null,2))}
  function exportResultsCsv(){if(result)downloadBlob(`${result.thread_id}_comments.csv`,exportCsv(result.comments),'text/csv;charset=utf-8')}
  async function refreshRecent(){setLoadingRecent(true);try{const r=await fetch('/api/recent?limit=30');if(!r.ok)throw new Error(`HTTP ${r.status}`);setRecent(await r.json())}catch(e){setRecent({storage_enabled:false,note:e.message})}finally{setLoadingRecent(false)}}
  function switchTab(tab){setActive(tab);setMobileMenu(false);if(tab==='history')refreshRecent();if(tab==='review_stats')refreshReviewStats()}

  const commentCount = result?.comments?.length||rows.length
  const toxicCount = result?.comments?.filter(x=>x.toxic_for_moderation).length||0
  const targetCount = result?new Set(result.comments.map(x=>x.target_user_id).filter(Boolean)).size:0
  const status = STATUS[result?.risk_level]||STATUS.none

  return <div className="app-shell">
    <aside className={`sidebar ${mobileMenu?'sidebar-open':''}`}>
      <div className="brand"><div className="brand-symbol"><Shield size={23}/><span/></div><div><strong>Shield<span>VI</span></strong><small>AI MODERATION LAB</small></div></div>
      <div className="nav-label">KHÔNG GIAN LÀM VIỆC</div>
      <nav className="side-nav" aria-label="Điều hướng chính">
        <button className={active==='analyze'?'active':''} onClick={()=>switchTab('analyze')}><LayoutDashboard size={19}/> Phân tích hội thoại <span className="nav-dot"/></button>
        <button className={active==='history'?'active':''} onClick={()=>switchTab('history')}><Clock3 size={19}/> Lịch sử phân tích</button>
        <button className={active==='review_stats'?'active':''} onClick={()=>switchTab('review_stats')}><BarChart3 size={19}/> Thống kê kiểm duyệt</button>
      </nav>
      <div className="nav-label lower">THÔNG TIN HỆ THỐNG</div>
      <div className="side-info"><div><Activity size={17}/><span>{result?.model_name || 'ViSoBERT'}</span></div><div><GitBranch size={17}/><span>Target + Repeated</span></div><div><ShieldCheck size={17}/><span>Hỗ trợ kiểm duyệt</span></div></div>
      <div className="sidebar-bottom"><div className="sidebar-protection"><ShieldCheck size={20}/><strong>Privacy by design</strong><p>Mặc định không lưu nội dung hội thoại trên máy chủ.</p></div><div className="side-footer">Đề tài nghiên cứu · Bản demo V3</div></div>
    </aside>
    {mobileMenu&&<button className="mobile-backdrop" onClick={()=>setMobileMenu(false)} aria-label="Đóng điều hướng"/>}
    <main className="main-content"><header className="topbar"><div className="breadcrumb"><button className="mobile-menu-btn" onClick={()=>setMobileMenu(true)} aria-label="Mở menu"><Menu size={22}/></button><span>ShieldVI</span><span className="slash">/</span><strong>{active==='analyze'?'Phân tích hội thoại':active==='history'?'Lịch sử':'Kiểm duyệt'}</strong></div><div className="topbar-right"><HeaderStatus health={health} loading={checking} onRetry={refreshHealth}/><span className="demo-badge">DEMO</span></div></header>
      <div className="page-body"><div className="page-heading"><div><div className="section-overline"><span className="overline-dot"/> HỆ THỐNG GIÁM SÁT HỘI THOẠI</div><h1>{active==='analyze'?'Phân tích hội thoại':active==='history'?'Lịch sử phân tích':'Thống kê kiểm duyệt'}</h1><p>{active==='analyze'?'Phát hiện ngôn ngữ độc hại, đối tượng bị nhắm tới và các dấu hiệu công kích lặp lại trong tiếng Việt.':active==='history'?'Xem lại các phiên phân tích được lưu dưới dạng metadata.':'Nhãn thủ công và các lỗi AI đã được lưu vào SQLite.'}</p></div><div className="heading-right"><span className="badge-research"><Sparkles size={15}/> AI + Lexical Review V3</span></div></div>
      {active==='analyze'?<>
        <div className="hero-banner"><div className="hero-copy"><span className="hero-tag"><span/> VIETNAMESE CYBERBULLYING ANALYSIS</span><h2>Hiểu hội thoại.<br/><span>Nhận diện rủi ro.</span></h2><p>ViSoBERT + phân tích quan hệ trả lời + bằng chứng công kích lặp lại, trong một giao diện duy nhất.</p><div className="hero-tags"><span><Check size={13}/> ViSoBERT V1</span><span><Check size={13}/> Target Detection</span><span><Check size={13}/> Explainable Alerts</span></div></div><div className="hero-art"><div className="hero-arc one"/><div className="hero-arc two"/><div className="hero-ring"><ShieldCheck size={60} strokeWidth={1.4}/></div><div className="hero-ping ping-one"/><div className="hero-ping ping-two"/></div></div>
        <div className="metrics"><MetricCard icon={MessageSquareMore} label="Bình luận trong hội thoại" value={commentCount} sub={result?'Đã được phân tích (AI + từ điển)':'Sẵn sàng phân tích'}/><MetricCard icon={AlertTriangle} label="Bình luận nghi toxic" value={result?toxicCount:'—'} sub={result?'Theo ngưỡng kiểm duyệt':'Chưa có kết quả'} tone="red"/><MetricCard icon={Users} label="Target suy luận" value={result?targetCount:'—'} sub="Target suy luận, có thể sai" tone="blue"/><MetricCard icon={ShieldAlert} label="Mức rủi ro" value={result?`${result.risk_score_heuristic}/100`:'—'} sub={result?status.title:'Chưa phân tích'} tone="teal"/></div>
        {error&&<div className="error-banner" role="alert"><AlertCircle size={19}/><div><strong>Không thể hoàn tất phân tích</strong><p>{error}</p></div><button onClick={()=>setError('')} aria-label="Đóng lỗi"><X size={17}/></button></div>}
        {!health?.model_loaded && !checking && <div className="connection-hint"><Info size={16}/><span>Backend chưa nạp ViSoBERT hoặc chưa kết nối. Chạy FastAPI với MODEL_PATH hợp lệ trên máy chủ rồi nhấn làm mới trạng thái.</span></div>}
        <div className="workspace-grid"><ThreadEditor {...{threadId,setThreadId,profile,setProfile,rows,setRows,busy}} onAnalyze={analyze} onSample={loadSample} onImport={()=>importRef.current?.click()} onExport={exportInput}/><div className="right-stack"><RiskGauge result={result}/><EvidencePanel result={result}/></div></div>
        <ResultsTable result={result} rows={rows} onExportCsv={exportResultsCsv} onExportJson={exportResult} reviewLabels={reviewLabels} onReview={onReview} onExportReviews={exportReviews} reviewerId={reviewerId} setReviewerId={setReviewerId} onSaveReviews={saveReviews} onLoadReviews={loadReviews} savingReviews={savingReviews} reviewStatus={reviewStatus}/>
        <div className="lower-grid"><NetworkGraph result={result} rows={rows}/><WarningPanel result={result}/></div>
        <input ref={importRef} type="file" accept=".json,application/json" onChange={importJson} hidden/>
      </>:active==='history'?<RecentTab recent={recent} loading={loadingRecent} onRefresh={refreshRecent}/>:<ReviewStatsTab stats={reviewStats} busy={loadingReviewStats} onRefresh={refreshReviewStats} onExport={exportDatabase}/>}<footer className="footer"><span>ShieldVI Research Prototype © 2026</span><span><Shield size={13}/> Không dùng cảnh báo tự động làm kết luận về con người.</span></footer></div>
    </main>
  </div>
}
