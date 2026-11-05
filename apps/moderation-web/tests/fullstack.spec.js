import {test,expect} from '@playwright/test'
import {randomUUID} from 'node:crypto'
import {writeFile,rename} from 'node:fs/promises'
import {execFile} from 'node:child_process'
import {promisify} from 'node:util'

const run=promisify(execFile),social=process.env.SOCIAL_WEB_TEST_URL
const password=process.env.SOCIAL_WEB_TEST_PASSWORD
const metrics={synthetic_ai:true,real_model_inference:false,processes:['social-api','ai-fixture','worker','social-web','moderation-web'],measurements:{}}
async function fault(mode){
  const file=process.env.SHIELDVI_AI_FAULT_FILE
  await writeFile(file+'.next',JSON.stringify({mode}),'utf8');await rename(file+'.next',file)
}
async function stats(){
  const result=await run(process.env.SHIELDVI_TEST_PYTHON,['-m','shieldvi_social.worker','--stats'],
    {cwd:process.env.SHIELDVI_TEST_SERVICE,env:process.env,windowsHide:true,timeout:15000})
  return JSON.parse(result.stdout)
}
async function loginAdmin(page){
  await page.goto('/');await page.getByLabel('Tên tài khoản',{exact:true}).fill('fixture_mod')
  await page.getByLabel('Mật khẩu',{exact:true}).fill(password)
  await page.getByRole('button',{name:'Đăng nhập kiểm duyệt',exact:true}).click()
  await expect(page.getByRole('heading',{name:/Mỗi quyết định/})).toBeVisible()
}

test('five-process register -> AI moderation -> outage/admin offline -> review -> appeal -> recovery',async({page,browser})=>{
  test.setTimeout(120000)
  const userContext=await browser.newContext(),author=await userContext.newPage()
  const seen=[]
  author.on('request',r=>seen.push(r.url()));page.on('request',r=>seen.push(r.url()))
  try{
    const username='e2e_'+randomUUID().slice(0,8)
    await author.goto(social)
    await author.getByRole('button',{name:'Đăng ký',exact:true}).click()
    await author.getByLabel('Tên tài khoản',{exact:true}).fill(username)
    await author.getByLabel('Email',{exact:true}).fill('E2E_PRIVATE_EMAIL_019@example.com')
    await author.getByLabel('Mật khẩu',{exact:true}).fill(password)
    await author.getByRole('button',{name:'Tạo tài khoản',exact:true}).click()
    await expect(author.getByRole('heading',{name:/Bảng tin của bạn/})).toBeVisible()

    // A slow AI proves that content creation returns pending before inference.
    await fault('delayed')
    const before=Date.now()
    await author.getByLabel('Nội dung bài viết',{exact:true}).fill('E2E benign root post')
    const createdPromise=author.waitForResponse(r=>r.url().endsWith('/api/v1/posts')&&r.request().method()==='POST')
    await author.getByRole('button',{name:'Gửi bài viết',exact:true}).click()
    const createdResponse=await createdPromise,created=await createdResponse.json()
    metrics.measurements.post_create_ms=Date.now()-before
    expect(createdResponse.status()).toBe(201);expect(created.visibility_status).toBe('PENDING_MODERATION')
    await expect(author.getByText('E2E benign root post',{exact:true})).toBeVisible()
    await expect.poll(async()=>{
      await author.getByRole('button',{name:'Làm mới',exact:true}).click()
      return author.locator('.content-card').first().innerText()
    },{timeout:30000,intervals:[300,500]}).toContain('Đã công khai')
    metrics.measurements.create_to_public_ms=Date.now()-before
    await fault('normal')
    const toxic='[TEST_TOXIC] E2E synthetic comment'
    await author.getByLabel('Viết bình luận',{exact:true}).fill(toxic)
    const commentPromise=author.waitForResponse(r=>r.url().endsWith(`/posts/${created.id}/comments`)&&r.request().method()==='POST')
    await author.getByRole('button',{name:'Gửi bình luận',exact:true}).click()
    const comment=await (await commentPromise).json()
    await expect.poll(async()=>{
      await author.getByRole('button',{name:'Làm mới',exact:true}).click()
      return author.getByRole('article').filter({hasText:toxic}).innerText()
    },{timeout:15000,intervals:[300,500]}).toContain('chờ xem xét')
    // No staff login or queue request has occurred: the worker operates with admin offline.
    metrics.admin_offline_auto_publish_verified=true

    await fault('unavailable')
    const privateBody='E2E_PRIVATE_CONTENT_019'
    await author.getByLabel('Viết bình luận',{exact:true}).fill(privateBody)
    const pendingPromise=author.waitForResponse(r=>r.url().endsWith(`/posts/${created.id}/comments`)&&r.request().method()==='POST')
    await author.getByRole('button',{name:'Gửi bình luận',exact:true}).click()
    const pending=await (await pendingPromise).json(),outageStart=Date.now()
    expect(pending.visibility_status).toBe('PENDING_MODERATION')
    await expect.poll(async()=>{const value=await stats();return value.counts.RETRY_WAIT||0},
      {timeout:15000,intervals:[300,500]}).toBeGreaterThan(0)
    metrics.measurements.outage_to_retry_observed_ms=Date.now()-outageStart
    const retryStats=await stats();metrics.retry_observed=retryStats.retry_attempts>=0
    await author.getByRole('button',{name:'Làm mới',exact:true}).click()
    await expect(author.getByRole('article').filter({hasText:privateBody})).toContainText('Đang chờ kiểm tra')

    await loginAdmin(page)
    await page.getByLabel('Loại nội dung').selectOption('comment')
    await page.locator('.queue-item').filter({hasText:privateBody}).click()
    await expect(page.locator('.evidence')).toContainText('Chưa có kết quả AI')
    await page.getByLabel('Lý do quyết định',{exact:true}).fill('Synthetic offline manual review')
    await page.getByRole('button',{name:'Ẩn nội dung',exact:true}).click()
    await expect(page.locator('.states')).toContainText('Đang ẩn')
    await author.getByRole('button',{name:'Nội dung & kháng nghị',exact:true}).click()
    const item=author.getByRole('article',{name:'Nội dung của tôi'}).filter({hasText:privateBody})
    await item.getByLabel('Lý do kháng nghị',{exact:true}).fill('Synthetic appeal with context')
    await item.getByRole('button',{name:'Gửi kháng nghị',exact:true}).click()
    await expect(item).toContainText('Đang chờ xem xét')
    await page.getByRole('button',{name:'Kháng nghị',exact:true}).click()
    await page.locator('.queue-item').filter({hasText:privateBody}).click()
    await page.getByLabel('Lý do quyết định',{exact:true}).fill('Synthetic appeal accepted')
    await page.getByRole('button',{name:'Chấp nhận · khôi phục',exact:true}).click()
    await expect(page.locator('.audit')).toContainText('APPEAL_RESOLVED')
    await expect(page.locator('.states')).toContainText('Đã công khai')

    await fault('normal')
    await author.getByRole('button',{name:'Làm mới trạng thái',exact:true}).click()
    await expect(item).toContainText('Đã được khôi phục')
    // New work proves the worker reconnects after 503. Existing manual verdict remains.
    await author.getByRole('button',{name:'Bảng tin',exact:true}).click()
    await author.getByLabel('Nội dung bài viết',{exact:true}).fill('E2E post after AI recovery')
    await author.getByRole('button',{name:'Gửi bài viết',exact:true}).click()
    await expect.poll(async()=>{
      await author.getByRole('button',{name:'Làm mới',exact:true}).click()
      return author.locator('.content-card').first().innerText()
    },{timeout:15000,intervals:[300,500]}).toContain('Đã công khai')
    await page.getByRole('button',{name:'Tải lại chi tiết',exact:true}).click()
    await expect(page.locator('.states')).toContainText('RESOLVED')
    await expect(page.locator('.audit')).toContainText('Synthetic appeal accepted')
    metrics.worker_recovery_and_manual_guard_verified=true
    metrics.browser_ai_requests=seen.filter(url=>url.startsWith(process.env.SOCIAL_AI_BASE_URL)).length
    expect(metrics.browser_ai_requests).toBe(0)
    metrics.final_worker_stats=await stats()
    metrics.total_synthetic_appeals_resolved=1
    metrics.appeal_overturn_fraction_synthetic=1
    await writeFile(process.env.SHIELDVI_E2E_METRICS,JSON.stringify(metrics,null,2)+'\n','utf8')
    await page.screenshot({path:process.env.PW_OUTPUT_DIR+'/appeal-after-worker-recovery.png',fullPage:false})
  }finally{
    await fault('normal');await userContext.close()
  }
})
