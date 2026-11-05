export function bodyLength(value) { return Array.from(value).length }
export function validBody(value) { return value.trim().length > 0 && bodyLength(value) <= 8000 && !value.includes('\0') }
export function authorName(id, user) { return id === user.id ? user.username : `Thành viên ${id.slice(0, 6)}` }
export function initials(name) { return name.slice(0, 2).toUpperCase() }
export function dateLabel(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(date)
}
export function getRoute() {
  if (window.location.pathname.replace(/\/$/, '') === '/my-moderation') return 'moderation'
  const match = window.location.pathname.match(/^\/posts\/([0-9a-f-]{36})\/?$/i)
  return match ? match[1] : null
}
export function commentDepth(row, items) {
  const byId = new Map(items.map(item => [item.id, item]))
  const seen = new Set([row.id])
  let depth = 0, parent = row.parent_id
  while (parent && byId.has(parent) && !seen.has(parent)) {
    seen.add(parent); depth++; parent = byId.get(parent).parent_id
  }
  return Math.min(depth, 3)
}
