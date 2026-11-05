import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ArrowRight, BookmarkCheck, Check, Eye, EyeOff, Feather, HeartHandshake, Home, Leaf, LogOut, MessageCircle, RefreshCw, ShieldCheck, Sparkles } from 'lucide-react'
import { createApi } from './api.js'
import { Avatar, Brand, Composer, ContentCard, ErrorNotice, Loading, PageControls, Status } from './components.jsx'
import PostDetail from './Thread.jsx'
import MyModeration from './MyModeration.jsx'
import { getRoute } from './utils.js'

const registrationEnabled = import.meta.env.VITE_REGISTRATION_ENABLED === 'true'

function AuthPage({ onAuthenticated, notice }) {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [visible, setVisible] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const pending = useRef(null)
  useEffect(() => () => pending.current?.abort(), [])
  function changeMode(value) { setMode(value); setError(''); setPassword(''); setVisible(false) }
  async function submit(event) {
    event.preventDefault()
    if (busy || (mode === 'register' && !registrationEnabled)) return
    const controller = new AbortController(); pending.current = controller
    setBusy(true); setError('')
    try {
      const api = createApi()
      if (mode === 'register') await api.register({ username, email, password }, controller.signal)
      const login = await api.login({ username, password }, controller.signal)
      const user = await createApi(login.access_token).me(controller.signal)
      if (!controller.signal.aborted) {
        setPassword('')
        onAuthenticated({ token: login.access_token, user, expiresAt: Date.now() + login.expires_in * 1000 })
      }
    } catch (error) { if (error.name !== 'AbortError') setError(error.message) }
    finally { if (!controller.signal.aborted) setBusy(false) }
  }
  const closed = mode === 'register' && !registrationEnabled
  return <div className="auth-page">
    <header className="auth-header"><Brand /><span className="private-label"><span />Không gian thử nghiệm</span></header>
    <main id="main-content" className="auth-main">
      <section className="auth-story" aria-labelledby="welcome-heading">
        <span className="eyebrow"><Leaf size={15} aria-hidden="true" />MỘT KHÔNG GIAN, NHIỀU GÓC NHÌN</span>
        <h1 id="welcome-heading">Kết nối bằng<br />{' '}những điều <span>tử tế.</span></h1>
        <p className="story-description">Chia sẻ câu chuyện của bạn. Lắng nghe một góc nhìn mới. Cùng xây dựng những cuộc trò chuyện mà ai cũng muốn tham gia.</p>
        <div className="conversation-art" aria-hidden="true"><div className="art-orbit" /><div className="art-bubble bubble-one"><span className="art-dot"><Feather size={19} /></span>Mỗi góc nhìn đều đáng được lắng nghe.<span className="bubble-line" /></div><div className="art-bubble bubble-two"><HeartHandshake size={22} /><div>Một chút tôn trọng.<br /><strong>Nhiều kết nối hơn.</strong></div><span className="art-spark">✦</span></div><div className="art-caption"><ShieldCheck size={15} />Chia sẻ có trách nhiệm</div></div>
        <div className="story-values"><span><Check size={15} aria-hidden="true" />Tôn trọng sự khác biệt</span><span><Check size={15} aria-hidden="true" />Trò chuyện an toàn hơn</span></div>
      </section>
      <section className="auth-card" aria-labelledby="auth-heading">
        <div className="auth-card-icon"><MessageCircle size={23} aria-hidden="true" /></div>
        <h2 id="auth-heading">{mode === 'login' ? 'Rất vui được gặp lại bạn' : 'Bắt đầu câu chuyện của bạn'}</h2>
        <p className="muted">{mode === 'login' ? 'Đăng nhập để tiếp tục kết nối cùng ShieldVI.' : 'Tạo tài khoản trong phiên thử nghiệm được cho phép.'}</p>
        <div className="auth-tabs" aria-label="Chọn đăng nhập hoặc đăng ký"><button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => changeMode('login')} disabled={busy}>Đăng nhập</button><button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => changeMode('register')} disabled={busy}>Đăng ký</button></div>
        {notice && <p className="session-notice" role="status">{notice}</p>}
        <ErrorNotice message={error} />
        {closed && <p className="session-notice" role="status">Đăng ký hiện đang giới hạn. Hãy dùng tài khoản thử nghiệm đã được cấp.</p>}
        <form onSubmit={submit} className="auth-form" aria-label={mode === 'login' ? 'Đăng nhập' : 'Đăng ký'} aria-busy={busy}>
          <label htmlFor="username">Tên tài khoản<input id="username" autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} required minLength={3} maxLength={30} pattern="[A-Za-z0-9_]+" placeholder="Tên tài khoản của bạn" disabled={busy || closed} aria-describedby={mode === 'register' ? 'username-help' : undefined} /></label>
          {mode === 'register' && <><small id="username-help">3–30 ký tự: chữ không dấu, số hoặc dấu gạch dưới.</small><label htmlFor="email">Email<input id="email" type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} maxLength={254} required disabled={busy || closed} placeholder="Email của bạn" /></label></>}
          <label htmlFor="password">Mật khẩu<span className="password-field"><input id="password" type={visible ? 'text' : 'password'} autoComplete={mode === 'register' ? 'new-password' : 'current-password'} value={password} onChange={e => setPassword(e.target.value)} required minLength={mode === 'register' ? 12 : 1} maxLength={128} placeholder={mode === 'register' ? 'Từ 12 đến 128 ký tự' : 'Nhập mật khẩu'} disabled={busy || closed} /><button className="password-toggle" type="button" aria-label={visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} aria-pressed={visible} onClick={() => setVisible(!visible)} disabled={busy || closed}>{visible ? <EyeOff size={17} aria-hidden="true" /> : <Eye size={17} aria-hidden="true" />}</button></span></label>
          <button className="button primary auth-submit" disabled={busy || closed}>{busy ? 'Đang kết nối…' : mode === 'login' ? 'Đăng nhập' : 'Tạo tài khoản'}<ArrowRight size={17} aria-hidden="true" /></button>
        </form>
        <p className="auth-footnote"><ShieldCheck size={15} aria-hidden="true" />Bạn cần đăng nhập lại sau khi tải lại hoặc đóng trang.</p>
      </section>
    </main>
    <footer className="auth-footer"><span>© {new Date().getFullYear()} ShieldVI Social</span><span>Kết nối có ý nghĩa. Chia sẻ có trách nhiệm.</span></footer>
  </div>
}

function Feed({ api, user, navigate, onCreated }) {
  const [data, setData] = useState(null)
  const [page, setPage] = useState(1)
  const [version, refresh] = useState(0)
  const [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    setData(null); setError('')
    api.feed(page, controller.signal).then(data => { if (!controller.signal.aborted) setData(data) }).catch(error => { if (!controller.signal.aborted && error.name !== 'AbortError') setError(error.message) })
    return () => controller.abort()
  }, [api, page, version])
  async function submit(body, key) {
    const row = await api.createPost(body, key)
    onCreated(row); navigate(row.id)
  }
  return <>
    <div className="page-heading"><div><p className="eyebrow">KHÔNG GIAN CHUNG</p><h1>Bảng tin của bạn<span className="heading-dot">.</span></h1><p className="muted">Những câu chuyện, góc nhìn và kết nối mới.</p></div><button className="icon-button refresh-button" title="Làm mới bảng tin" aria-label="Làm mới bảng tin" onClick={() => refresh(value => value + 1)}><RefreshCw size={18} aria-hidden="true" /></button></div>
    <section className="post-composer card" aria-label="Tạo bài viết"><div className="composer-person"><Avatar name={user.username} /><div><strong>Chào {user.username},</strong><p>Hôm nay bạn muốn chia sẻ điều gì?</p></div><Feather size={20} className="muted-icon" aria-hidden="true" /></div><Composer label="Nội dung bài viết" placeholder="Một câu chuyện nhỏ, một góc nhìn mới…" submitLabel="Gửi bài viết" onSubmit={submit} /></section>
    <div className="feed-heading"><span><span className="live-dot" />Bài viết công khai</span><span>Sắp xếp theo mới nhất</span></div>
    <ErrorNotice message={error} retry={() => refresh(value => value + 1)} />
    {!data && !error && <Loading text="Đang tải bảng tin…" />}
    {data && data.items.length === 0 && <section className="feed-empty card"><span className="empty-illustration"><Feather size={29} aria-hidden="true" /><span>✦</span></span><p className="eyebrow">MỘT KHỞI ĐẦU MỚI</p><h2>Nhường chỗ cho câu chuyện đầu tiên.</h2><p>Bảng tin sẽ hiển thị các bài viết đã công khai. Bài bạn vừa gửi vẫn có thể xem riêng trong lúc chờ kiểm tra.</p></section>}
    <div className="feed-list">{data?.items.map(row => <ContentCard key={`${row.id}:${row.content_revision}`} row={row} api={api} user={user} navigate={navigate} onChange={updated => { onCreated(updated); refresh(value => value + 1) }} />)}</div>
    <PageControls data={data} change={setPage} busy={!data} />
  </>
}

function SignedIn({ session, expired, onLogout }) {
  const { user, token } = session
  const scopeRef = useRef(null)
  useEffect(() => {
    const scope = new AbortController(); scopeRef.current = scope
    return () => { if (scopeRef.current === scope) scopeRef.current = null; scope.abort() }
  }, [])
  const api = useMemo(() => createApi(token, expired, () => scopeRef.current?.signal), [token, expired])
  const [route, setRoute] = useState(getRoute)
  const [recent, setRecent] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const headingRef = useRef(null)
  useEffect(() => {
    const pop = () => setRoute(getRoute())
    window.addEventListener('popstate', pop)
    return () => window.removeEventListener('popstate', pop)
  }, [])
  function navigate(id) {
    history.pushState(null, '', id ? `/posts/${id}` : '/')
    setRoute(id); setError(''); window.scrollTo({ top: 0 })
    requestAnimationFrame(() => headingRef.current?.focus())
  }
  function remember(row) { setRecent(items => [row, ...items.filter(item => item.id !== row.id)].slice(0, 10)) }
  async function logout() {
    setBusy(true); setError('')
    try { await api.logout(); scopeRef.current?.abort(); history.replaceState(null, '', '/'); onLogout() }
    catch (error) { if (error.status !== 401) setError('Chưa thể kết thúc phiên trên máy chủ. Vui lòng thử đăng xuất lại.') }
    finally { setBusy(false) }
  }
  return <div className="social-app">
    <a href="#main-content" className="skip-link">Chuyển đến nội dung chính</a>
    <header className="app-header"><div className="header-inner"><button className="brand-button" aria-label="ShieldVI Social — về bảng tin" onClick={() => navigate(null)}><Brand /></button><span className="header-mantra">Mỗi góc nhìn đều có một nơi để chia sẻ.</span><div className="header-account"><span className="private-label"><span />Phiên thử nghiệm</span><Avatar name={user.username} small /></div></div></header>
    <div className="app-layout">
      <aside className="left-sidebar"><div className="profile-card"><Avatar name={user.username} /><strong>{user.username}</strong><span>Không gian của bạn</span></div>
        <nav className="main-nav" aria-label="Điều hướng chính"><button className={!route ? 'active' : ''} onClick={() => navigate(null)} aria-current={!route ? 'page' : undefined}><Home size={19} aria-hidden="true" />Bảng tin<ArrowRight size={15} className="nav-arrow" aria-hidden="true" /></button><button className={route==='moderation'?'active':''} onClick={()=>{history.pushState(null,'','/my-moderation');setRoute('moderation')}} aria-current={route==='moderation'?'page':undefined}><ShieldCheck size={19}/>Nội dung & kháng nghị</button></nav>
        {recent.length > 0 && <div className="recent-posts"><h2><BookmarkCheck size={15} aria-hidden="true" />Bài vừa gửi</h2>{recent.map(row => <button key={row.id} onClick={() => navigate(row.id)} className={route === row.id ? 'selected' : ''}><span className="recent-title">{row.body?.slice(0, 70) || 'Bài viết đã xóa'}</span><Status row={row} /></button>)}<p>Danh sách trong phiên hiện tại.</p></div>}
        <div className="sidebar-bottom"><p><Leaf size={15} aria-hidden="true" />Cùng giữ cuộc trò chuyện tử tế.</p><button className="logout-button" onClick={logout} disabled={busy}><LogOut size={17} aria-hidden="true" />{busy ? 'Đang đăng xuất…' : 'Đăng xuất'}</button></div>
      </aside>
      <main className="main-column" id="main-content" tabIndex={-1} ref={headingRef}>
        <ErrorNotice message={error} />
        {route==='moderation'?<MyModeration api={api}/>:route ? <PostDetail key={route} id={route} api={api} user={user} navigate={navigate} onUpdate={remember} /> : <Feed api={api} user={user} navigate={navigate} onCreated={remember} />}
        <footer className="feed-footer"><ShieldCheck size={14} aria-hidden="true" />Một cộng đồng tốt đẹp bắt đầu từ cách chúng ta trò chuyện.</footer>
      </main>
      <aside className="right-sidebar" aria-label="Thông tin cộng đồng"><section className="welcome-note"><span className="eyebrow">Ở ĐÂY, BẠN ĐƯỢC LẮNG NGHE</span><div className="note-icon"><HeartHandshake size={32} aria-hidden="true" /></div><h2>Góc nhìn khác nhau.<br />Sự tôn trọng như nhau.</h2><p>Một lời góp ý chân thành có thể mở ra một cuộc trò chuyện tốt đẹp.</p><span className="note-line" /></section><section className="community-guide"><h2><Sparkles size={17} aria-hidden="true" />Cùng chia sẻ tốt hơn</h2><ol><li><span>01</span><div><strong>Nói về ý tưởng</strong><p>Trao đổi quan điểm, tôn trọng người đối diện.</p></div></li><li><span>02</span><div><strong>Lắng nghe trước khi trả lời</strong><p>Mỗi người đều có một câu chuyện riêng.</p></div></li><li><span>03</span><div><strong>Chia sẻ có trách nhiệm</strong><p>Giữ thông tin riêng tư cho chính bạn.</p></div></li></ol></section><div className="review-note"><ShieldCheck size={18} aria-hidden="true" /><p>Nội dung mới được lưu riêng trong lúc chờ kiểm tra. Bạn luôn thấy trạng thái thực tế.</p></div><p className="side-copyright">ShieldVI Social · {new Date().getFullYear()}</p></aside>
    </div>
  </div>
}

export default function App() {
  const [session, setSession] = useState(null)
  const [notice, setNotice] = useState('')
  const liveSession = useRef(null)
  const expired = useCallback(token => {
    if (liveSession.current?.token !== token) return
    liveSession.current = null; setSession(null)
    setNotice('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
  }, [])
  function authenticated(value) { liveSession.current = value; setNotice(''); setSession(value) }
  function logout() { liveSession.current = null; setSession(null); setNotice('Bạn đã đăng xuất an toàn.') }
  useEffect(() => {
    if (!session) return
    const timeout = setTimeout(() => expired(session.token), Math.max(0, session.expiresAt - Date.now()))
    return () => clearTimeout(timeout)
  }, [session, expired])
  return session ? <SignedIn key={session.token} session={session} expired={expired} onLogout={logout} /> : <AuthPage notice={notice} onAuthenticated={authenticated} />
}
