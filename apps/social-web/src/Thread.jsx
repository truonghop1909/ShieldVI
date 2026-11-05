import React, { useEffect, useRef, useState } from 'react'
import { ArrowLeft, MessageCircle, RefreshCw, X } from 'lucide-react'
import { Composer, ContentCard, ErrorNotice, Loading, PageControls } from './components.jsx'
import { authorName, commentDepth } from './utils.js'

function Comments({ post, api, user }) {
  const [page, setPage] = useState(1)
  const [version, refresh] = useState(0)
  const [data, setData] = useState(null)
  const [created, setCreated] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(true)
  const [reply, setReply] = useState(null)
  const [notice, setNotice] = useState('')
  const composerRef = useRef(null)
  useEffect(() => {
    const controller = new AbortController()
    setBusy(true); setData(null); setError(''); setReply(null)
    api.comments(post.id, page, controller.signal).then(data => { if (!controller.signal.aborted) setData(data) }).catch(error => {
      if (!controller.signal.aborted && error.name !== 'AbortError') { setError(error.message); setCreated([]) }
    }).finally(() => { if (!controller.signal.aborted) setBusy(false) })
    return () => controller.abort()
  }, [api, post.id, page, version])
  async function submit(body, key) {
    const row = await api.createComment(post.id, body, reply?.id || null, key)
    setCreated(items => [row, ...items.filter(item => item.id !== row.id)])
    setReply(null); setNotice('Bình luận đã được lưu và đang chờ kiểm tra. Chưa công khai với mọi người.')
    refresh(value => value + 1)
  }
  function update(row) {
    setCreated(items => items.map(item => item.id === row.id ? row : item))
    setData(null); setReply(null); refresh(value => value + 1)
    setNotice(row.visibility_status === 'DELETED_BY_AUTHOR' ? 'Đã xóa bình luận.' : 'Đã lưu thay đổi. Bình luận đang chờ kiểm tra lại.')
  }
  function chooseReply(row) {
    setReply(row); setNotice('')
    requestAnimationFrame(() => composerRef.current?.querySelector('textarea')?.focus())
  }
  const items = data ? [...data.items, ...created.filter(row => row.visibility_status !== 'DELETED_BY_AUTHOR' && !data.items.some(item => item.id === row.id))] : []
  return <section className="thread" aria-labelledby="comments-heading">
    <div className="section-heading"><h2 id="comments-heading">Cuộc trò chuyện</h2><span className="count-label">{data ? `${data.total} bình luận bạn có thể xem` : ''}</span></div>
    <div className="comment-composer" ref={composerRef}>
      {reply && <div className="reply-banner"><div><span>Đang trả lời {authorName(reply.author_id, user)}</span><blockquote>{reply.body}</blockquote></div><button className="icon-button" aria-label="Hủy trả lời" onClick={() => setReply(null)}><X size={16} aria-hidden="true" /></button></div>}
      <Composer key={reply?.id || 'root'} label={reply ? 'Nội dung trả lời' : 'Viết bình luận'} placeholder="Thêm góc nhìn của bạn…" submitLabel={reply ? 'Gửi trả lời' : 'Gửi bình luận'} onSubmit={submit} />
    </div>
    {notice && <p className="success-notice" role="status">{notice}</p>}
    {busy && <Loading text="Đang tải cuộc trò chuyện…" />}
    <ErrorNotice message={error} retry={() => refresh(value => value + 1)} />
    {!busy && !error && items.length === 0 && <div className="empty-comments"><MessageCircle size={25} aria-hidden="true" /><p>Cuộc trò chuyện bắt đầu từ bạn.</p><span>Chia sẻ một bình luận tôn trọng và có ý nghĩa.</span></div>}
    <div className="comment-list">{items.map(row => <ContentCard key={row.id} row={row} user={user} api={api} kind="comments" depth={commentDepth(row, items)} onChange={update} reply={chooseReply} />)}</div>
    <PageControls data={data} busy={busy} change={setPage} />
  </section>
}

export default function PostDetail({ id, api, user, navigate, onUpdate }) {
  const [post, setPost] = useState(null)
  const [error, setError] = useState('')
  const [version, refresh] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setPost(null); setError('')
    api.post(id, controller.signal).then(data => { if (!controller.signal.aborted) setPost(data) }).catch(error => { if (!controller.signal.aborted && error.name !== 'AbortError') setError(error.message) })
    return () => controller.abort()
  }, [api, id, version])
  function update(row) { setPost(row); onUpdate(row) }
  return <>
    <div className="detail-heading"><button className="text-button" onClick={() => navigate(null)}><ArrowLeft size={16} aria-hidden="true" />Bảng tin</button><button className="text-button" onClick={() => refresh(value => value + 1)}><RefreshCw size={15} aria-hidden="true" />Làm mới</button></div>
    <h1 className="detail-title" tabIndex={-1}>Câu chuyện & cuộc trò chuyện</h1>
    <ErrorNotice message={error} retry={() => refresh(value => value + 1)} />
    {!post && !error && <Loading />}
    {post && <>
      <ContentCard row={post} user={user} api={api} detail onChange={update} />
      {['PENDING_MODERATION', 'HELD_FOR_REVIEW', 'HIDDEN'].includes(post.visibility_status) && <div className="pending-explanation"><strong>Nội dung hiện chưa công khai</strong><p>Bạn vẫn có thể xem nội dung của mình. Chọn “Làm mới” để cập nhật trạng thái khi có kết quả kiểm tra.</p></div>}
      {post.visibility_status !== 'DELETED_BY_AUTHOR' && <Comments key={`${post.id}:${post.content_revision}:${post.decision_version}`} post={post} api={api} user={user} />}
    </>}
  </>
}
