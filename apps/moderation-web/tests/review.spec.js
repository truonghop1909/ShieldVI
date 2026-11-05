import {test,expect} from '@playwright/test'
import path from 'node:path'
import fs from 'node:fs'
const password=process.env.SOCIAL_WEB_TEST_PASSWORD
const social=process.env.SOCIAL_WEB_TEST_URL
const publicPost='10000000-0000-4000-8000-000000000001'
const screenshots=process.env.PW_OUTPUT_DIR||'test-results'
test.beforeAll(()=>fs.mkdirSync(screenshots,{recursive:true}))
async function adminLogin(page,name='fixture_mod'){
  await page.goto('/');await page.getByLabel('Tên tài khoản',{exact:true}).fill(name);await page.getByLabel('Mật khẩu',{exact:true}).fill(password)
  await page.getByRole('button',{name:'Đăng nhập kiểm duyệt'}).click()
  if(name!=='fixture_author')await expect(page.getByRole('heading',{name:/Mỗi quyết định/})).toBeVisible()
}
async function socialLogin(page,name='fixture_author'){
  await page.goto(social);await page.getByLabel('Tên tài khoản',{exact:true}).fill(name);await page.getByLabel('Mật khẩu',{exact:true}).fill(password)
  await page.getByRole('form',{name:'Đăng nhập',exact:true}).getByRole('button',{name:'Đăng nhập',exact:true}).click();await expect(page.getByRole('heading',{name:/Bảng tin của bạn/})).toBeVisible()
}

test('comment -> manual hide -> author appeal -> restore -> audit survives reload',async({page,browser})=>{
  const userContext=await browser.newContext(),author=await userContext.newPage()
  try{
    await socialLogin(author);await author.goto(`${social}/posts/${publicPost}`)
    // Reload requires re-login; the post URL remains selected.
    await author.getByLabel('Tên tài khoản',{exact:true}).fill('fixture_author');await author.getByLabel('Mật khẩu',{exact:true}).fill(password)
    await author.getByRole('form',{name:'Đăng nhập',exact:true}).getByRole('button',{name:'Đăng nhập',exact:true}).click()
    const body='Browser appeal lifecycle comment'
    await author.getByLabel('Viết bình luận',{exact:true}).fill(body)
    await author.getByRole('button',{name:'Gửi bình luận',exact:true}).click()
    await expect(author.getByText(body,{exact:true})).toBeVisible()
    await adminLogin(page)
    await page.getByLabel('Loại nội dung').selectOption('comment')
    await page.locator('.queue-item').filter({hasText:body}).click()
    await expect(page.getByRole('button',{name:'Ẩn nội dung',exact:true})).toBeDisabled()
    await page.getByLabel('Lý do quyết định',{exact:true}).fill('Cần xem lại ngữ cảnh')
    await page.getByRole('button',{name:'Ẩn nội dung',exact:true}).click()
    await expect(page.locator('.states')).toContainText('Đang ẩn')
    await author.getByRole('button',{name:'Nội dung & kháng nghị',exact:true}).click()
    const item=author.getByRole('article',{name:'Nội dung của tôi'}).filter({hasText:body})
    await expect(item).toContainText('Cần xem lại ngữ cảnh')
    await item.getByLabel('Lý do kháng nghị',{exact:true}).fill('Đây là lời giải thích, xin xem lại')
    await item.getByRole('button',{name:'Gửi kháng nghị',exact:true}).click()
    await expect(item).toContainText('Đang chờ xem xét')
    await expect(item).toContainText('Đang tạm ẩn')
    await page.getByRole('button',{name:'Kháng nghị',exact:true}).click()
    await page.locator('.queue-item').filter({hasText:body}).click()
    await expect(page.locator('.appeal')).toContainText('Đây là lời giải thích')
    await page.getByLabel('Lý do quyết định',{exact:true}).fill('Đã đối chiếu ngữ cảnh, khôi phục')
    await page.getByRole('button',{name:'Chấp nhận · khôi phục',exact:true}).click()
    await expect(page.locator('.states')).toContainText('Đã công khai')
    await expect(page.locator('.audit')).toContainText('APPEAL_RESOLVED')
    await author.getByRole('button',{name:'Làm mới trạng thái',exact:true}).click()
    await expect(item).toContainText('Đã được khôi phục')
    await expect(item).toContainText('Đã công khai')
    await page.reload();await adminLogin(page)
    await page.getByRole('button',{name:'Tất cả',exact:true}).click();await page.getByLabel('Loại nội dung').selectOption('comment')
    await page.locator('.queue-item').filter({hasText:body}).click()
    await expect(page.locator('.audit')).toContainText('APPEAL_RESOLVED')
  }finally{await userContext.close()}
})

test('AI provenance, literal XSS, false positive feedback, mobile layouts',async({page})=>{
  await adminLogin(page)
  await page.getByRole('button',{name:'Tất cả',exact:true}).click()
  // The AI fixture is on the second page, after older pending fixtures.
  let row=page.locator('.queue-item').filter({hasText:'Evidence fixture'})
  if(!await row.count()){await page.getByRole('button',{name:'Sau',exact:true}).click()}
  await row.click()
  await expect(page.locator('.full-text')).toContainText('<img src=x onerror=')
  expect(await page.evaluate(()=>window.__adminXss)).toBeUndefined()
  await expect(page.locator('.evidence')).toContainText('browser-synthetic-not-real-inference')
  await expect(page.locator('.states')).toContainText('TOXIC')
  await expect(page.locator('.states')).toContainText('REVIEW')
  await page.screenshot({path:path.join(screenshots,'desktop-dashboard.png'),fullPage:false})
  for(const width of [390,320]){
    await page.setViewportSize({width,height:844})
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
  }
  await page.locator('.review-detail').scrollIntoViewIfNeeded()
  await page.screenshot({path:path.join(screenshots,'mobile-detail.png'),fullPage:false})
  await page.getByLabel('Lý do quyết định',{exact:true}).fill('Trích dẫn cần ngữ cảnh, cảnh báo nhầm')
  await page.getByLabel(/Ghi nhận cảnh báo nhầm/).check()
  await page.getByRole('button',{name:'Cho phép đăng',exact:true}).click()
  await expect(page.locator('.audit')).toContainText('MANUAL_APPROVE')
  await page.locator('.audit').getByText('Metadata quyết định',{exact:true}).first().click()
  await expect(page.locator('.audit')).toContainText('"false_positive": true')
})

test('failed queue supports manual decisions without AI; 409 retains draft',async({page})=>{
  await adminLogin(page,'fixture_admin')
  await page.getByRole('button',{name:'AI lỗi',exact:true}).click()
  await page.locator('.queue-item').filter({hasText:'Offline failed fixture'}).click()
  await expect(page.locator('.evidence')).toContainText('AI_TIMEOUT')
  await expect(page.locator('.evidence')).toContainText('Chưa có kết quả AI')
  await page.getByLabel('Lý do quyết định',{exact:true}).fill('Duyệt thủ công khi offline')
  await page.route('**/api/v1/moderation/decisions',route=>route.fulfill({status:409,contentType:'application/json',body:'{}'}))
  await page.getByRole('button',{name:'Cho phép đăng',exact:true}).click()
  await expect(page.getByRole('alert')).toContainText('Phiên bản')
  await expect(page.getByRole('textbox',{name:'Lý do quyết định',exact:true})).toHaveValue('Duyệt thủ công khi offline')
  await page.unroute('**/api/v1/moderation/decisions')
  await page.getByRole('button',{name:'Cho phép đăng',exact:true}).click()
  await expect(page.locator('.states')).toContainText('Đã công khai')
})

test('report form -> staff Reports tab, no automatic hiding',async({page,browser})=>{
  const context=await browser.newContext(),viewer=await context.newPage()
  try{
    await socialLogin(viewer,'fixture_viewer')
    const card=viewer.getByRole('article').filter({hasText:'Cau chuyen demo cong khai'})
    await card.getByText('Báo cáo nội dung',{exact:true}).click()
    await card.getByLabel('Lý do báo cáo',{exact:true}).fill('Báo cáo qua trình duyệt')
    await card.getByRole('button',{name:'Gửi báo cáo',exact:true}).click()
    await expect(card).toContainText('Đã nhận báo cáo')
    await expect(card).toContainText('Đã công khai')
    await adminLogin(page);await page.getByRole('button',{name:'Báo cáo',exact:true}).click()
    await page.locator('.queue-item').filter({hasText:'Cau chuyen demo cong khai'}).click()
    await expect(page.locator('.review-detail')).toContainText('Báo cáo qua trình duyệt')
  }finally{await context.close()}
})

test('non-staff denied, no token storage, reload and 401 remove private content',async({page})=>{
  await adminLogin(page,'fixture_author')
  await expect(page.getByRole('alert')).toContainText('Chỉ tài khoản')
  await adminLogin(page)
  expect(await page.evaluate(()=>[localStorage.length,sessionStorage.length])).toEqual([0,0])
  await page.route('**/api/v1/moderation/queue?**',route=>route.fulfill({status:401,body:'{}',contentType:'application/json'}))
  await page.getByRole('button',{name:'Làm mới hàng chờ',exact:true}).click()
  await expect(page.getByRole('button',{name:'Đăng nhập kiểm duyệt'})).toBeVisible()
  await expect(page.locator('.queue')).toHaveCount(0)
})

test('queue errors and logout failure stay recoverable',async({page})=>{
  await adminLogin(page)
  await page.route('**/api/v1/moderation/queue?**',route=>route.fulfill({status:429,body:'{}',contentType:'application/json'}))
  await page.getByRole('button',{name:'Làm mới hàng chờ',exact:true}).click()
  await expect(page.getByRole('alert')).toContainText('quá nhanh')
  await page.unroute('**/api/v1/moderation/queue?**')
  await page.getByRole('button',{name:'Làm mới hàng chờ',exact:true}).click()
  await expect(page.locator('.queue-item').first()).toBeVisible()
  await page.route('**/api/v1/auth/logout',route=>route.fulfill({status:503,body:'{}',contentType:'application/json'}))
  await page.getByRole('button',{name:'Đăng xuất',exact:true}).click()
  await expect(page.getByRole('alert')).toContainText('Máy chủ')
  await expect(page.locator('.queue')).toBeVisible()
  await page.unroute('**/api/v1/auth/logout')
  await page.getByRole('button',{name:'Đăng xuất',exact:true}).click()
  await expect(page.getByRole('button',{name:'Đăng nhập kiểm duyệt'})).toBeVisible()
})
