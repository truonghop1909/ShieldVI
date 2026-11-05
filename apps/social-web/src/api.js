const configuredBase = (import.meta.env.VITE_SOCIAL_API_BASE || '').trim()
if (configuredBase) {
  const parsed = new URL(configuredBase)
  if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password || parsed.pathname !== '/' || parsed.search || parsed.hash) {
    throw new Error('VITE_SOCIAL_API_BASE must be an exact HTTP(S) origin')
  }
}
const base = configuredBase.replace(/\/$/, '')

export class ApiError extends Error {
  constructor(status, message) { super(message); this.status = status }
}

function friendlyMessage(status, action, retryAfter) {
  if (status === 401) return action === 'login' ? 'Tên tài khoản hoặc mật khẩu chưa đúng.' : 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.'
  if (status === 403) return action === 'register' ? 'Đăng ký đang tắt trong phiên thử nghiệm này. Vui lòng liên hệ người quản trị.' : 'Bạn không có quyền thực hiện thao tác này.'
  if (status === 404) return 'Nội dung không tồn tại hoặc hiện chưa được chia sẻ với bạn.'
  if (status === 409) return action === 'register' ? 'Không thể đăng ký với thông tin này. Hãy kiểm tra tên tài khoản và email.' : 'Nội dung đã thay đổi. Hãy tải lại phiên bản mới nhất trước khi thử tiếp.'
  if (status === 413) return 'Nội dung quá lớn. Hãy rút gọn rồi thử lại.'
  if (status === 422) return action === 'register' ? 'Kiểm tra tên tài khoản, email và mật khẩu (12–128 ký tự).' : 'Thông tin chưa hợp lệ. Hãy kiểm tra nội dung rồi thử lại.'
  if (status === 429) return `Bạn thao tác hơi nhanh. Vui lòng thử lại${/^\d{1,4}$/.test(retryAfter || '') ? ` sau ${retryAfter} giây` : ' sau một lát'}.`
  return 'Máy chủ chưa thể xử lý yêu cầu. Nội dung đang soạn vẫn được giữ để bạn thử lại.'
}

export function createApi(token = null, onExpired = () => {}, getScopeSignal = () => null) {
  async function request(path, { method = 'GET', body, signal, key, action } = {}) {
    const scope = getScopeSignal()
    const effectiveSignal = signal && scope ? AbortSignal.any([signal, scope]) : signal || scope || undefined
    const headers = { Accept: 'application/json' }
    if (body !== undefined) headers['Content-Type'] = 'application/json'
    if (token) headers.Authorization = `Bearer ${token}`
    if (key) headers['Idempotency-Key'] = key
    let response
    try {
      response = await fetch(`${base}/api/v1${path}`, {
        method, headers, credentials: 'omit', cache: 'no-store', signal: effectiveSignal,
        body: body === undefined ? undefined : JSON.stringify(body),
      })
    } catch (error) {
      if (error.name === 'AbortError') throw error
      throw new ApiError(0, 'Không kết nối được máy chủ. Hãy kiểm tra kết nối rồi thử lại.')
    }
    if (effectiveSignal?.aborted) throw new DOMException('Request canceled', 'AbortError')
    if (!response.ok) {
      if (response.status === 401 && token) onExpired(token)
      throw new ApiError(response.status, friendlyMessage(response.status, action, response.headers.get('Retry-After')))
    }
    if (response.status === 204) return null
    try {
      const data = await response.json()
      if (effectiveSignal?.aborted) throw new DOMException('Request canceled', 'AbortError')
      return data
    } catch (error) {
      if (error.name === 'AbortError') throw error
      throw new ApiError(0, 'Phản hồi từ máy chủ chưa hợp lệ. Vui lòng tải lại.')
    }
  }
  return {
    register: (body, signal) => request('/auth/register', { method: 'POST', body, signal, action: 'register' }),
    login: (body, signal) => request('/auth/login', { method: 'POST', body, signal, action: 'login' }),
    me: signal => request('/me', { signal }), logout: () => request('/auth/logout', { method: 'POST' }),
    myModeration: (page, signal) => request(`/me/moderation?page=${page}&page_size=10`, { signal }),
    appeal: (kind, row, reason, signal) => request(`/content/${kind}/${row.id}/appeals`, {method:'POST',signal,body:{expected_revision:row.content_revision,expected_decision_version:row.decision_version,reason}}),
    report: (kind, row, reason, signal) => request(`/content/${kind}/${row.id}/reports`, {method:'POST',signal,body:{expected_revision:row.content_revision,expected_decision_version:row.decision_version,reason}}),
    feed: (page, signal) => request(`/feed?page=${page}&page_size=10`, { signal }),
    post: (id, signal) => request(`/posts/${encodeURIComponent(id)}`, { signal }),
    comments: (id, page, signal) => request(`/posts/${encodeURIComponent(id)}/comments?page=${page}&page_size=20`, { signal }),
    createPost: (body, key) => request('/posts', { method: 'POST', body: { body }, key }),
    createComment: (id, body, parent_id, key) => request(`/posts/${encodeURIComponent(id)}/comments`, { method: 'POST', body: { body, parent_id }, key }),
    edit: (kind, row, body) => request(`/${kind}/${row.id}`, { method: 'PATCH', body: { body, expected_revision: row.content_revision, expected_decision_version: row.decision_version } }),
    remove: (kind, row) => request(`/${kind}/${row.id}`, { method: 'DELETE', body: { expected_revision: row.content_revision, expected_decision_version: row.decision_version } }),
  }
}
