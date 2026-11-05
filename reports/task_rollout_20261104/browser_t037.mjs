import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
const require=createRequire(new URL('../../apps/social-web/package.json',import.meta.url)),{chromium,expect}=require('@playwright/test')
const out=process.env.LIVE_TEST_ARTIFACTS,web=process.env.LIVE_TEST_WEB,ai=process.env.LIVE_TEST_AI,thread=process.env.LIVE_TEST_THREAD,password=process.env.LIVE_TEST_PASSWORD,serviceToken=process.env.SOCIAL_AI_SERVICE_TOKEN
const checks=[],latencies=[];const browser=await chromium.launch({channel:'chrome',headless:true})
const contextA=await browser.newContext({viewport:{width:1440,height:1050}}),contextB=await browser.newContext({viewport:{width:1100,height:900}})
const a=await contextA.newPage(),b=await contextB.newPage();let streamRequests=0
for(const page of [a,b])page.on('request',r=>{if(r.url().includes('/events?since='))streamRequests++})
async function login(page,username){await page.goto(`${web}/live.html?thread=${thread}`,{waitUntil:'domcontentloaded'});await page.getByLabel('Tên tài khoản').fill(username);await page.getByLabel('Mật khẩu',{exact:true}).fill(password);await page.getByRole('button',{name:'Đăng nhập',exact:true}).click();await expect(page.locator('.live-root')).toContainText('Synthetic realtime fixture',{timeout:15000});await expect(page.getByTestId('live-connection')).toHaveText('Đã kết nối trực tiếp',{timeout:10000})}
async function send(page,text,observer){const started=Date.now();await page.getByLabel('Nội dung tin nhắn',{exact:true}).fill(text);const ack=page.waitForResponse(r=>r.url().includes(`/threads/${thread}/messages`)&&r.request().method()==='POST');await page.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click();const response=await ack;assert([200,201].includes(response.status()));const row=await response.json();const ack_ms=Date.now()-started;if(observer)await expect(observer.locator('.live-body').filter({hasText:text})).toHaveCount(1,{timeout:20000});latencies.push({condition:'fixture_AI_workflow',ack_ms,observer_delivery_ms:Date.now()-started});return row}
async function outage(offline){const result=await fetch(ai+'/__test/state',{method:'POST',headers:{Authorization:`Bearer ${serviceToken}`,'Content-Type':'application/json'},body:JSON.stringify({offline})});assert.equal(result.status,200)}
try{
 await login(a,'live_alice');await login(b,'live_bob');checks.push('two_independent_authenticated_browser_contexts')
 const first=await send(a,'LIVE_BENIGN: Mình chia sẻ lịch buổi gặp cuối tuần.',b);checks.push('send_ack_and_two_client_delivery_without_refresh')
 await expect(a.locator(`[data-comment-id="${first.id}"]`)).toContainText('AI: COMPLETED',{timeout:15000})
 await b.locator(`[data-comment-id="${first.id}"]`).getByRole('button',{name:'Trả lời',exact:true}).click()
 const reply=await send(b,'LIVE_REPLY: Mình tham gia, cảm ơn bạn.',a);assert.equal(reply.parent_id,first.id);checks.push('parent_reply_persisted')
 await contextB.setOffline(true)
 const recovered=await send(a,'LIVE_RECONNECT: Tin gửi khi người đọc mất mạng.')
 await new Promise(resolve=>setTimeout(resolve,700));await contextB.setOffline(false)
 await expect(b.locator('.live-body').filter({hasText:'LIVE_RECONNECT:'})).toHaveCount(1,{timeout:20000});checks.push('automatic_reconnect_cursor_catchup')
 await outage(true)
 const delayed=await send(a,'LIVE_AI_OFFLINE: Tin vẫn được lưu khi AI lỗi503.')
 await expect(a.locator(`[data-comment-id="${delayed.id}"]`)).toContainText('AI: RETRYING',{timeout:15000})
 await expect(b.locator('.live-body').filter({hasText:'LIVE_AI_OFFLINE:'})).toHaveCount(0)
 await outage(false);await expect(b.locator('.live-body').filter({hasText:'LIVE_AI_OFFLINE:'})).toHaveCount(1,{timeout:20000});checks.push('ai_outage_send_persistence_retry_and_recovery')
 await a.locator(`[data-comment-id="${first.id}"]`).getByRole('button',{name:'Sửa',exact:true}).click();await a.getByLabel('Sửa nội dung').fill('LIVE_EDITED: Lịch đã đổi sang sáng chủ nhật.');await a.getByRole('button',{name:'Lưu thay đổi',exact:true}).click()
 await expect(b.locator('.live-body').filter({hasText:'LIVE_EDITED:'})).toHaveCount(1,{timeout:20000});checks.push('edit_updates_peer_without_stale_body')
 await a.locator(`[data-comment-id="${first.id}"]`).getByRole('button',{name:'Xóa',exact:true}).click();await expect(b.locator('.live-body').filter({hasText:'LIVE_EDITED:'})).toHaveCount(0,{timeout:10000});checks.push('delete_updates_peer')
 await b.reload({waitUntil:'domcontentloaded'});await expect(b.locator('.live-body').filter({hasText:'LIVE_REPLY:'})).toHaveCount(1,{timeout:15000});await expect(b.locator('.live-body').filter({hasText:'LIVE_AI_OFFLINE:'})).toHaveCount(1);checks.push('reload_restores_server_messages_and_session')
 let failFirst=true
 await a.route(`**/api/live/threads/${thread}/messages`,async route=>{const response=await route.fetch();if(failFirst){failFirst=false;await route.abort('failed')}else await route.fulfill({response})})
 await a.getByLabel('Nội dung tin nhắn',{exact:true}).fill('LIVE_ACK_LOST: Chỉ lưu một lần dù gửi lại.')
 await a.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click();await expect(a.getByRole('alert')).toContainText('Nội dung vẫn được giữ',{timeout:15000})
 await a.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click();await expect(b.locator('.live-body').filter({hasText:'LIVE_ACK_LOST:'})).toHaveCount(1,{timeout:20000});await a.unroute(`**/api/live/threads/${thread}/messages`);checks.push('lost_ack_retry_idempotent_no_duplicate')
 const xss='<img src=x onerror="window.__live_xss=1"> LIVE_TEXT_ONLY'
 await send(a,xss,b);assert.equal(await b.locator('img').count(),0);assert.equal(await b.evaluate(()=>window.__live_xss),undefined);checks.push('untrusted_text_rendered_without_html_execution')
 const rbac=await b.evaluate(async()=>{const token=sessionStorage.getItem('shieldvi-live-session');return (await fetch('/api/v1/moderation/queue',{headers:{Authorization:`Bearer ${token}`}})).status});assert.equal(rbac,403);checks.push('ordinary_user_admin_api_denied')
 assert(streamRequests>=2);assert.equal(await b.locator('body').getByText('toxicity_score',{exact:false}).count(),0);checks.push('sse_used_no_staff_raw_evidence_in_user_ui')
 await a.screenshot({path:path.join(out,'T037_client_A.png'),fullPage:true});await b.setViewportSize({width:390,height:844});await b.screenshot({path:path.join(out,'T037_client_B_mobile.png'),fullPage:true})
 fs.writeFileSync(path.join(out,'T037_browser_result.json'),JSON.stringify({status:'PASS',checks,latencies,stream_requests:streamRequests,contexts:2,ai_mode:'deterministic_raw_fixture_actual_default_v5_rules_not_neural',no_page_refresh_required:true},null,2))
 console.log(JSON.stringify({status:'PASS',checks:checks.length,contexts:2,stream_requests:streamRequests}))
}finally{await contextA.close();await contextB.close();await browser.close()}
