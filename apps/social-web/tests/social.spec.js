import { test, expect } from '@playwright/test'
import { randomUUID } from 'node:crypto'
import path from 'node:path'

const password = process.env.SOCIAL_WEB_TEST_PASSWORD
const postId = '10000000-0000-4000-8000-000000000001'
const shot = name => path.join(process.env.PW_OUTPUT_DIR || 'test-results', name)

async function login(page) {
  await page.goto('/')
  await page.getByLabel('Tên tài khoản').fill('fixture_viewer')
  await page.getByLabel('Mật khẩu', { exact: true }).fill(password)
  await page.getByRole('form', { name: 'Đăng nhập', exact: true }).getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Bảng tin của bạn.' })).toBeVisible()
}

test('register, publish pending, comment, reply, edit, delete and logout with real API', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'Đăng ký', exact: true }).click()
  const username = `web_${randomUUID().slice(0, 8)}`
  await page.getByLabel('Tên tài khoản').fill(username)
  await page.getByLabel('Email', { exact: true }).fill(`${username}@example.com`)
  await page.getByLabel('Mật khẩu', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Bảng tin của bạn.' })).toBeVisible()
  await page.getByLabel('Nội dung bài viết', { exact: true }).fill('Câu chuyện thử nghiệm từ trình duyệt thật.')
  await page.getByRole('button', { name: 'Gửi bài viết', exact: true }).click()
  await expect(page).toHaveURL(/\/posts\/[0-9a-f-]+$/)
  await expect(page.getByText('Nội dung hiện chưa công khai')).toBeVisible()
  await expect(page.getByRole('article', { name: `Bài viết của ${username}` }).getByText('Câu chuyện thử nghiệm từ trình duyệt thật.', { exact: true })).toBeVisible()
  await page.getByLabel('Viết bình luận', { exact: true }).fill('Bình luận gốc đang chờ kiểm tra.')
  await page.getByRole('button', { name: 'Gửi bình luận', exact: true }).click()
  await expect(page.getByText('1 bình luận bạn có thể xem')).toBeVisible()
  const root = page.getByRole('article', { name: `Bình luận của ${username}` }).filter({ hasText: 'Bình luận gốc đang chờ kiểm tra.' })
  await root.getByRole('button', { name: 'Trả lời', exact: true }).click()
  await page.getByLabel('Nội dung trả lời', { exact: true }).fill('Một câu trả lời có parent thật.')
  await page.getByRole('button', { name: 'Gửi trả lời', exact: true }).click()
  await expect(page.getByText('2 bình luận bạn có thể xem')).toBeVisible()
  await expect(page.getByText('Một câu trả lời có parent thật.', { exact: true })).toBeVisible()
  const article = page.getByRole('article', { name: `Bài viết của ${username}` })
  await article.getByRole('button', { name: 'Sửa nội dung', exact: true }).click()
  await article.getByRole('textbox', { name: 'Sửa nội dung', exact: true }).fill('Nội dung đã sửa — vẫn pending.')
  await article.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click()
  await expect(article.getByText('Nội dung đã sửa — vẫn pending.', { exact: true })).toBeVisible()
  page.once('dialog', dialog => dialog.accept())
  await article.getByRole('button', { name: 'Xóa nội dung', exact: true }).click()
  await expect(page.getByText('Nội dung này đã được tác giả xóa.')).toBeVisible()
  await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await expect(page.getByText('Bạn đã đăng xuất an toàn.')).toBeVisible()
  await expect(page.getByText('Nội dung đã sửa — vẫn pending.', { exact: true })).toHaveCount(0)
})

test('feed pagination and real private content permissions', async ({ page }) => {
  await login(page)
  await expect(page.getByText('Câu chuyện công khai 01. Một góc nhìn mới để cùng lắng nghe.')).toBeVisible()
  await expect(page.getByText('TOP-SECRET-FIXTURE')).toHaveCount(0)
  await page.getByRole('button', { name: 'Sau', exact: true }).click()
  await expect(page.getByText('Câu chuyện công khai 11. Một góc nhìn mới để cùng lắng nghe.')).toBeVisible()
  await page.getByRole('button', { name: 'Trước', exact: true }).click()
  await expect(page.getByText('Câu chuyện công khai 01. Một góc nhìn mới để cùng lắng nghe.')).toBeVisible()
  await page.screenshot({ path: shot('desktop-feed.png'), fullPage: true })
  // Client-side navigation keeps the memory session, then real API must deny the private ID.
  await page.evaluate(() => { history.pushState(null, '', '/posts/10000000-0000-4000-8000-0000000000f0'); dispatchEvent(new PopStateEvent('popstate')) })
  await expect(page.getByRole('alert')).toContainText('hiện chưa được chia sẻ với bạn')
  await expect(page.getByText('TOP-SECRET-FIXTURE')).toHaveCount(0)
})

test('escaped full text, reply and mobile layout', async ({ page }) => {
  await login(page)
  await page.evaluate(id => { history.pushState(null, '', `/posts/${id}`); dispatchEvent(new PopStateEvent('popstate')) }, postId)
  const literal = page.getByText(/<img src=x onerror="window.__shieldviXss=1">/)
  await expect(literal).toBeVisible()
  await expect(page.locator('.comment-list img, .comment-list script')).toHaveCount(0)
  expect(await page.evaluate(() => window.__shieldviXss)).toBeUndefined()
  await page.getByRole('button', { name: 'Trả lời', exact: true }).click()
  await expect(page.getByLabel('Nội dung trả lời', { exact: true })).toBeFocused()
  await page.getByLabel('Nội dung trả lời', { exact: true }).fill('Bình luận responsive trên điện thoại.')
  await page.getByRole('button', { name: 'Gửi trả lời', exact: true }).click()
  await expect(page.getByText('Bình luận responsive trên điện thoại.', { exact: true })).toBeVisible()
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 })
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy()
    expect(await literal.evaluate(element => element.scrollWidth <= element.clientWidth + 1)).toBeTruthy()
  }
  await page.screenshot({ path: shot('mobile-thread.png'), fullPage: true })
})

test('network retry preserves draft and uses the same idempotency key', async ({ page }) => {
  await login(page)
  const keys = [], statuses = []
  let first = true
  await page.route('**/api/v1/posts', async route => {
    if (route.request().method() !== 'POST') return route.continue()
    keys.push(route.request().headers()['idempotency-key'])
    const response = await route.fetch()
    statuses.push(response.status())
    if (first) { first = false; return route.abort('failed') }
    return route.fulfill({ response })
  })
  await page.getByLabel('Nội dung bài viết', { exact: true }).fill('Giữ bản nháp khi kết nối bị ngắt.')
  await page.getByRole('button', { name: 'Gửi bài viết', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('Không kết nối được máy chủ')
  await expect(page.getByLabel('Nội dung bài viết', { exact: true })).toHaveValue('Giữ bản nháp khi kết nối bị ngắt.')
  await page.getByRole('button', { name: 'Gửi bài viết', exact: true }).click()
  await expect(page).toHaveURL(/\/posts\//)
  expect(keys).toHaveLength(2)
  expect(keys[0]).toBe(keys[1])
  expect(statuses).toEqual([201, 200])
})

test('401 clears session and browser storage contains no token', async ({ page }) => {
  await login(page)
  expect(await page.evaluate(() => ({ local: { ...localStorage }, session: { ...sessionStorage } }))).toEqual({ local: {}, session: {} })
  await page.route('**/api/v1/feed?*', route => route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"expired"}' }))
  await page.getByRole('button', { name: 'Làm mới bảng tin', exact: true }).click()
  await expect(page.getByText('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')).toBeVisible()
  await expect(page.getByLabel('Nội dung bài viết', { exact: true })).toHaveCount(0)
  await page.unroute('**/api/v1/feed?*')
  await login(page)
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Rất vui được gặp lại bạn' })).toBeVisible()
})

test('backend registration-disabled, validation and rate limit errors are honest', async ({ page }) => {
  await page.goto('/')
  await page.screenshot({ path: shot('desktop-login.png'), fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy()
  await page.screenshot({ path: shot('mobile-login.png'), fullPage: true })
  await page.getByRole('button', { name: 'Đăng ký', exact: true }).click()
  await page.getByLabel('Tên tài khoản').fill('blocked_fixture')
  await page.getByLabel('Email', { exact: true }).fill('blocked@example.com')
  await page.getByLabel('Mật khẩu', { exact: true }).fill(password)
  await page.route('**/api/v1/auth/register', route => route.fulfill({ status: 403, contentType: 'application/json', body: '{}' }))
  await page.getByRole('button', { name: 'Tạo tài khoản', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('Đăng ký đang tắt')
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).first().click()
  await page.getByLabel('Tên tài khoản').fill('fixture_viewer')
  await page.getByLabel('Mật khẩu', { exact: true }).fill(password)
  await page.route('**/api/v1/auth/login', route => route.fulfill({ status: 429, headers: { 'Retry-After':'7' }, contentType: 'application/json', body: '{}' }))
  await page.getByRole('form', { name: 'Đăng nhập', exact: true }).getByRole('button', { name: 'Đăng nhập', exact: true }).click()
  await expect(page.getByRole('alert')).toContainText('sau 7 giây')
})

test('newer decision conflict and failed logout keep the UI truthful', async ({ page }) => {
  await login(page)
  await page.getByLabel('Nội dung bài viết', { exact: true }).fill('Bản gốc dùng kiểm tra conflict.')
  await page.getByRole('button', { name: 'Gửi bài viết', exact: true }).click()
  await expect(page.getByText('Nội dung hiện chưa công khai')).toBeVisible()
  const article = page.getByRole('article', { name: 'Bài viết của fixture_viewer' })
  await article.getByRole('button', { name: 'Sửa nội dung', exact: true }).click()
  await article.getByRole('textbox', { name: 'Sửa nội dung', exact: true }).fill('Bản nháp chưa được máy chủ chấp nhận.')
  await page.route('**/api/v1/posts/*', route => route.request().method() === 'PATCH' ? route.fulfill({ status:409, contentType:'application/json', body:'{}' }) : route.continue())
  await article.getByRole('button', { name: 'Lưu thay đổi', exact: true }).click()
  await expect(article.getByRole('alert')).toContainText('Nội dung đã thay đổi')
  await expect(article.getByRole('textbox', { name: 'Sửa nội dung', exact: true })).toHaveValue('Bản nháp chưa được máy chủ chấp nhận.')
  await page.route('**/api/v1/auth/logout', route => route.abort('failed'))
  await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await expect(page.getByRole('alert').filter({ hasText: 'Chưa thể kết thúc phiên' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Câu chuyện & cuộc trò chuyện' })).toBeVisible()
})

test('server-provided session deadline returns to login', async ({ page }) => {
  await page.route('**/api/v1/auth/login', async route => {
    const response = await route.fetch()
    const body = await response.json()
    await route.fulfill({ response, json: { ...body, expires_in: 1 } })
  })
  await login(page)
  await expect(page.getByText('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')).toBeVisible()
  await expect(page.getByLabel('Nội dung bài viết', { exact: true })).toHaveCount(0)
})

test('late create response after logout cannot reopen a private post', async ({ page }) => {
  await login(page)
  let release, arrived, completed
  const wait = new Promise(resolve => { release = resolve })
  const atServer = new Promise(resolve => { arrived = resolve })
  const done = new Promise(resolve => { completed = resolve })
  await page.route('**/api/v1/posts', async route => {
    const response = await route.fetch()
    arrived()
    await wait
    try { await route.fulfill({ response }) } catch { /* Browser may have canceled on logout. */ }
    completed()
  })
  await page.getByLabel('Nội dung bài viết', { exact: true }).fill('Kết quả phải bỏ qua sau đăng xuất.')
  await page.getByRole('button', { name: 'Gửi bài viết', exact: true }).click()
  await atServer
  await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click()
  await expect(page.getByText('Bạn đã đăng xuất an toàn.')).toBeVisible()
  release(); await done
  await expect(page).toHaveURL(/\/$/)
  await expect(page.getByRole('heading', { name: 'Rất vui được gặp lại bạn' })).toBeVisible()
})
