import React, { useId, useRef, useState } from 'react'
import { AlertCircle, ArrowLeft, ArrowRight, Check, Clock3, Link2, LoaderCircle, MessageCircle, Pencil, Send, ShieldCheck, Trash2 } from 'lucide-react'
import { authorName, bodyLength, dateLabel, initials, validBody } from './utils.js'
import { ReportForm } from './MyModeration.jsx'

export function Brand() {
  return <span className="brand"><span className="brand-mark"><ShieldCheck size={24} aria-hidden="true" /></span><span>Shield<span className="brand-vi">VI</span><span className="brand-sub">SOCIAL</span></span></span>
}
export function Avatar({ name, small = false }) {
  return <span className={`avatar ${small ? 'small' : ''}`} aria-hidden="true">{initials(name)}</span>
}
export function ErrorNotice({ message, retry }) {
  if (!message) return null
  return <div className="error-notice" role="alert"><AlertCircle size={18} aria-hidden="true" /><div><p>{message}</p>{retry && <button className="text-button" onClick={retry}>Thử lại</button>}</div></div>
}
export function Loading({ text = 'Đang tải nội dung…' }) {
  return <div className="loading" role="status"><LoaderCircle className="spin" size={21} aria-hidden="true" />{text}</div>
}
export function Status({ row }) {
  const state = row.visibility_status
  const status = {
    PENDING_MODERATION: ['pending', 'Đang chờ kiểm tra'], HELD_FOR_REVIEW: ['pending', 'Đang tạm giữ'],
    HIDDEN: ['hidden', 'Đang tạm ẩn'], DELETED_BY_AUTHOR: ['hidden', 'Đã xóa'],
    PUBLISHED_FLAGGED: ['published', 'Đã công khai · chờ xem xét'], PUBLISHED: ['published', 'Đã công khai'],
  }[state] || ['pending', 'Đang cập nhật trạng thái']
  return <span className={`status ${status[0]}`}>{status[0] === 'published' ? <Check size={13} aria-hidden="true" /> : <Clock3 size={13} aria-hidden="true" />}{status[1]}</span>
}

export function Composer({ label, placeholder, submitLabel, onSubmit, initial = '', onCancel, pendingHint = true }) {
  const id = useId()
  const [body, setBody] = useState(initial)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const attempt = useRef(null)
  const length = bodyLength(body)
  async function submit(event) {
    event.preventDefault()
    if (!validBody(body) || busy) return
    if (!attempt.current || attempt.current.body !== body) attempt.current = { body, key: crypto.randomUUID() }
    setBusy(true); setError('')
    try {
      await onSubmit(body, attempt.current.key)
      setBody(''); attempt.current = null
    } catch (error) { if (error.name !== 'AbortError') setError(error.message) }
    finally { setBusy(false) }
  }
  return <form className="composer" onSubmit={submit} aria-label={`Soạn: ${label}`} aria-busy={busy}>
    <label className="composer-label" htmlFor={id}>{label}</label>
    <textarea id={id} value={body} onChange={e => setBody(e.target.value)} placeholder={placeholder} maxLength={16000}
      rows={initial ? 5 : 3} disabled={busy} aria-describedby={`${id}-help ${id}-count`} />
    <ErrorNotice message={error} />
    <div className="composer-bottom"><span id={`${id}-help`} className="composer-hint">{pendingHint ? <><ShieldCheck size={15} aria-hidden="true" />Nội dung sẽ được kiểm tra trước khi công khai.</> : 'Lưu thay đổi sẽ đưa nội dung về trạng thái chờ kiểm tra.'}</span>
      <div className="composer-actions"><span id={`${id}-count`} className={length > 8000 ? 'over-limit' : 'char-count'}>{length.toLocaleString('vi-VN')}/8.000</span>
        {onCancel && <button type="button" className="button quiet" onClick={onCancel} disabled={busy}>Hủy</button>}
        <button className="button primary" disabled={busy || !validBody(body)}>{busy ? <LoaderCircle size={16} className="spin" aria-hidden="true" /> : <Send size={16} aria-hidden="true" />}{busy ? 'Đang lưu…' : submitLabel}</button>
      </div>
    </div>
  </form>
}

export function PageControls({ data, change, busy }) {
  if (!data || data.total <= data.page_size) return null
  const pages = Math.ceil(data.total / data.page_size)
  return <nav className="pagination" aria-label="Phân trang"><button className="button quiet" disabled={busy || data.page <= 1} onClick={() => change(data.page - 1)}><ArrowLeft size={15} aria-hidden="true" />Trước</button>
    <span>Trang {data.page} / {pages}</span><button className="button quiet" disabled={busy || data.page >= pages} onClick={() => change(data.page + 1)}>Sau<ArrowRight size={15} aria-hidden="true" /></button></nav>
}

export function ContentCard({ row, user, api, kind = 'posts', navigate, onChange, reply, detail = false, depth = 0 }) {
  const [editing, setEditing] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const own = row.author_id === user.id
  const deleted = row.visibility_status === 'DELETED_BY_AUTHOR'
  const name = authorName(row.author_id, user)
  async function remove() {
    if (!window.confirm('Xóa nội dung này? Người khác sẽ không còn xem được nội dung.')) return
    setBusy(true); setError('')
    try { onChange(await api.remove(kind, row)) }
    catch (error) { setError(error.message) }
    finally { setBusy(false) }
  }
  async function save(body) {
    const updated = await api.edit(kind, row, body)
    setEditing(false); onChange(updated)
  }
  async function copyLink() {
    try { await navigator.clipboard.writeText(`${window.location.origin}/posts/${row.id}`); setCopied(true) }
    catch { setError('Chưa thể sao chép liên kết. Bạn có thể mở bài viết và sao chép địa chỉ trên trình duyệt.') }
  }
  return <article className={`content-card ${kind === 'comments' ? 'comment-card' : ''}`} style={{ '--depth': depth }} aria-label={kind === 'comments' ? `Bình luận của ${name}` : `Bài viết của ${name}`}>
    <header className="content-header"><Avatar name={name} small={kind === 'comments'} /><div className="content-identity"><strong>{name}{own && <span className="you-label">Bạn</span>}</strong><time dateTime={row.created_at} title={new Date(row.created_at).toLocaleString('vi-VN')}>{dateLabel(row.created_at)}</time></div>
      {own && !deleted && <div className="content-actions"><button className="icon-button" title="Sửa nội dung" aria-label="Sửa nội dung" onClick={() => { setEditing(!editing); setError('') }} disabled={busy}><Pencil size={15} aria-hidden="true" /></button><button className="icon-button danger" title="Xóa nội dung" aria-label="Xóa nội dung" onClick={remove} disabled={busy}><Trash2 size={15} aria-hidden="true" /></button></div>}
    </header>
    <div className="content-status"><Status row={row} /></div>
    {row.parent_id && <p className="reply-context"><MessageCircle size={12} aria-hidden="true" />Trả lời một bình luận trong cuộc trò chuyện</p>}
    {editing ? <Composer label="Sửa nội dung" initial={row.body || ''} submitLabel="Lưu thay đổi" onSubmit={save} onCancel={() => setEditing(false)} pendingHint={false} /> : <p className={`content-body ${deleted ? 'deleted-copy' : ''}`}>{row.body ?? 'Nội dung này đã được tác giả xóa.'}</p>}
    <ErrorNotice message={error} />
    {!deleted && <footer className="content-footer">
      {kind === 'posts' && !detail && <button className="text-button" onClick={() => navigate(row.id)}><MessageCircle size={16} aria-hidden="true" />Xem cuộc trò chuyện<ArrowRight size={14} aria-hidden="true" /></button>}
      {reply && <button className="text-button" onClick={() => reply(row)}><MessageCircle size={14} aria-hidden="true" />Trả lời</button>}
      {kind === 'posts' && <button className="text-button copy-link" onClick={copyLink}><Link2 size={14} aria-hidden="true" />{copied ? 'Đã sao chép' : 'Sao chép liên kết'}</button>}
    </footer>}
    {!own && !deleted && ['PUBLISHED','PUBLISHED_FLAGGED'].includes(row.visibility_status) && <ReportForm key={`${row.id}:${row.content_revision}`} api={api} row={row} kind={kind}/>}
  </article>
}
