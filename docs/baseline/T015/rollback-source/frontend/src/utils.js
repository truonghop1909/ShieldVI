export const SAMPLE_THREAD = {
  thread_id: 'DEMO_A',
  profile: 'conservative',
  comments: [
    {comment_id:'d1',user_id:'U01',timestamp:'2026-10-10T10:00:00Z',text:'Mình mới đăng bản thiết kế, mọi người góp ý nhé.',parent_id:null,mentioned_user_ids:[]},
    {comment_id:'d2',user_id:'U02',timestamp:'2026-10-10T10:03:00Z',text:'Bạn chẳng biết gì mà cũng đăng bài sao?',parent_id:'d1',mentioned_user_ids:[]},
    {comment_id:'d3',user_id:'U01',timestamp:'2026-10-10T10:05:00Z',text:'Bạn có thể góp ý cụ thể hơn không?',parent_id:'d2',mentioned_user_ids:[]},
    {comment_id:'d4',user_id:'U02',timestamp:'2026-10-10T10:07:00Z',text:'Bài của bạn ngu ngốc thật đấy.',parent_id:'d3',mentioned_user_ids:[]},
    {comment_id:'d5',user_id:'U03',timestamp:'2026-10-10T10:12:00Z',text:'Màu sắc đẹp, nhưng nên tăng độ tương phản.',parent_id:'d1',mentioned_user_ids:[]}
  ]
}

export function nowLocalInput() {
  const d = new Date()
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function dateInput(timestamp) {
  if (!timestamp) return nowLocalInput()
  const d = new Date(timestamp)
  if (Number.isNaN(d.getTime())) return nowLocalInput()
  const pad = n => String(n).padStart(2,'0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function dateToISO(value) {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) throw new Error('Thời gian không hợp lệ')
  return d.toISOString()
}

export function makeEditable(comments) {
  return comments.map(c => ({
    comment_id: String(c.comment_id || ''),
    user_id: String(c.user_id || ''),
    text: String(c.text || ''),
    parent_id: c.parent_id || '',
    timestamp: dateInput(c.timestamp),
    mentioned_user_ids: Array.isArray(c.mentioned_user_ids) ? c.mentioned_user_ids.join(', ') : ''
  }))
}

export function requestFromEditor(threadId, profile, rows) {
  return {
    thread_id: threadId.trim(),
    profile,
    comments: rows.map(c => ({
      comment_id: c.comment_id.trim(),
      user_id: c.user_id.trim(),
      text: c.text.trim(),
      parent_id: c.parent_id?.trim() || null,
      timestamp: dateToISO(c.timestamp),
      mentioned_user_ids: (c.mentioned_user_ids || '').split(',').map(s=>s.trim()).filter(Boolean)
    }))
  }
}

export function validateInput(payload) {
  if (!payload.thread_id) throw new Error('Hãy nhập mã hội thoại.')
  if (!payload.comments?.length) throw new Error('Cần ít nhất một bình luận.')
  if (payload.comments.length > 500) throw new Error('Tối đa 500 bình luận mỗi lần phân tích.')
  const ids = new Set()
  for (const c of payload.comments) {
    if (!c.comment_id || !c.user_id || !c.text) throw new Error('Mỗi dòng cần comment_id, user_id và nội dung.')
    if (ids.has(c.comment_id)) throw new Error(`Trùng comment_id: ${c.comment_id}`)
    ids.add(c.comment_id)
    if (c.parent_id === c.comment_id) throw new Error(`${c.comment_id} không được tự trả lời chính mình.`)
  }
  for (const c of payload.comments) {
    if (c.parent_id && !ids.has(c.parent_id)) throw new Error(`${c.comment_id}: parent_id ${c.parent_id} không tồn tại.`)
  }
}

export function downloadBlob(name, content, type='application/json;charset=utf-8') {
  const a = document.createElement('a')
  const blob = new Blob([content], {type})
  const url = URL.createObjectURL(blob)
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(()=>URL.revokeObjectURL(url), 1000)
}

export function exportCsv(rows) {
  if (!rows.length) return ''
  const columns = ['comment_id','user_id','timestamp','toxicity_score','toxic_for_moderation','profanity_detected','lexical_review_recommended','directed_insult_candidate','lexical_matched_forms','toxic_for_repeated_rule','target_user_id','target_method','target_confidence']
  const escape = v => '"' + String(v == null ? '' : v).replace(/"/g,'""') + '"'
  return '\uFEFF' + [columns.join(','), ...rows.map(r=>columns.map(k=>escape(k==='lexical_matched_forms' ? (r.lexical_signals||[]).map(x=>x.matched_form).join(' | ') : r[k])).join(','))].join('\r\n')
}

export function friendlyError(res, data) {
  if (res.status === 503) return 'Mô hình ViSoBERT chưa được tải. Kiểm tra MODEL_PATH trên FastAPI.'
  const detail = data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map(x => `${x.loc?.join('.') || 'Dữ liệu'}: ${x.msg || 'không hợp lệ'}`).join('; ')
  return `Máy chủ trả về lỗi HTTP ${res.status}`
}
