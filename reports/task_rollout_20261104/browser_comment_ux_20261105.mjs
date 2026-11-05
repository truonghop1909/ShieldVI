// Real browser viewport/focus regression; existing UI tests auto-scrolled inputs.
import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
const require=createRequire(new URL('../../apps/social-web/package.json',import.meta.url)),{chromium,expect}=require('@playwright/test')
const out=process.env.LIVE_TEST_ARTIFACTS,thread=process.env.LIVE_TEST_THREAD,web=process.env.LIVE_TEST_WEB
const browser=await chromium.launch({channel:'chrome',headless:true}),context=await browser.newContext({viewport:{width:1050,height:720}}),page=await context.newPage()
const checks=[]
async function openCard(){
 await page.evaluate(()=>scrollTo(0,0))
 const card=page.locator(`[data-post-id="${thread}"]`)
 await card.getByRole('button',{name:'Xem bài và bình luận',exact:true}).click()
 const input=page.getByLabel('Nội dung tin nhắn',{exact:true})
 // No input.fill(), locator.scrollIntoViewIfNeeded() or focus() before assertions:
 // the application must make the composer discoverable by itself.
 await expect(input).toBeInViewport({timeout:10000})
 await expect(input).toBeFocused({timeout:10000})
 return input
}
try{
 await page.goto(web+'/live.html?thread='+thread)
 await page.getByLabel('Tên tài khoản').fill('live_alice');await page.getByLabel('Mật khẩu',{exact:true}).fill(process.env.LIVE_TEST_PASSWORD)
 await page.getByRole('button',{name:'Đăng nhập',exact:true}).click()
 await expect(page.getByTestId('live-connection')).toHaveText('Đã kết nối trực tiếp',{timeout:20000})
 if(process.env.LIVE_TEST_COMMENT_BUTTON_CHECK==='1'){
  await page.setViewportSize({width:1060,height:480})
  const action=page.getByRole('button',{name:'Viết bình luận',exact:true}),input=page.getByLabel('Nội dung tin nhắn',{exact:true})
  await expect(action).toBeVisible({timeout:8000});await action.click()
  await expect(input).toBeFocused();await expect(input).toBeInViewport({ratio:1})
  await expect(page.getByRole('button',{name:'Gửi tin nhắn',exact:true})).toBeInViewport({ratio:1})
  checks.push('write_comment_button_focuses_input_and_reveals_submit_on_short_screen')
  const composer=await page.locator('.live-composer').boundingBox(),pager=await page.getByRole('navigation',{name:'Phân trang hội thoại'}).boundingBox()
  expect(composer.y).toBeLessThan(pager.y);checks.push('composer_is_above_comment_list_and_pagination')
  await page.setViewportSize({width:1050,height:720})
 }
 const input=await openCard();checks.push('selected_post_composer_enters_viewport_and_keyboard_focus')
 await input.fill('Mình góp ý lịch sinh hoạt cho nhóm trong bản kiểm thử giao diện.')
 const responsePromise=page.waitForResponse(r=>r.url().includes('/messages')&&r.request().method()==='POST')
 await page.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click()
 const response=await responsePromise;expect(response.status()).toBe(201);const row=await response.json()
 await expect(page.locator(`[data-comment-id="${row.id}"] [title="COMPLETED"]`)).toBeVisible({timeout:30000})
 checks.push('comment_is_persisted_and_analyzed_by_actual_worker')
 await openCard();checks.push('reopening_same_post_refocuses_composer')
 const draft='Bản nháp cần được giữ khi có cập nhật trực tiếp.';await input.fill(draft)
 await page.getByLabel('Nội dung bài đăng',{exact:true}).focus()
 await page.waitForTimeout(1800)
 await expect(page.getByLabel('Nội dung bài đăng',{exact:true})).toBeFocused();await expect(input).toHaveValue(draft)
 checks.push('background_refresh_does_not_steal_focus_or_clear_draft')
 await page.setViewportSize({width:390,height:780});await openCard();checks.push('mobile_post_open_reveals_composer')
 await page.screenshot({path:path.join(out,'comment_ux.png'),fullPage:true})
 await page.setViewportSize({width:1366,height:900})
 await page.screenshot({path:path.join(out,'feed_desktop.png'),fullPage:true})
 fs.writeFileSync(path.join(out,'comment_ux_result.json'),JSON.stringify({status:'PASS',checks,actual_neural_inference:true,comment_id:row.id,no_training:true},null,2))
 console.log(JSON.stringify({status:'PASS',checks:checks.length}))
}catch(error){await page.screenshot({path:path.join(out,'comment_ux_failure.png'),fullPage:true}).catch(()=>{});throw error}
finally{await context.close();await browser.close()}
