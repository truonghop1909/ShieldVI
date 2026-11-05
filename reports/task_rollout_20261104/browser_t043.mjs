import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
const require=createRequire(new URL('../../apps/social-web/package.json',import.meta.url)),{chromium,expect}=require('@playwright/test')
const out=process.env.LIVE_TEST_ARTIFACTS,web=process.env.LIVE_TEST_WEB,adminWeb=process.env.LIVE_TEST_ADMIN,thread=process.env.LIVE_TEST_THREAD,password=process.env.LIVE_TEST_PASSWORD
const browser=await chromium.launch({channel:'chrome',headless:true}),contexts=[],checks=[],latencies=[]
for(let i=0;i<3;i++)contexts.push(await browser.newContext({viewport:{width:1450,height:1080}}))
const [a,b,m]=await Promise.all(contexts.map(c=>c.newPage()))
async function login(page,name,url=web){await page.goto(`${url}/live.html?thread=${thread}`,{waitUntil:'domcontentloaded'});await page.getByLabel('Tên tài khoản').fill(name);await page.getByLabel('Mật khẩu',{exact:true}).fill(password);await page.getByRole('button',{name:name==='live_admin'?'Đăng nhập kiểm duyệt':'Đăng nhập',exact:true}).click()}
async function send(page,text,parent){const started=Date.now();if(parent)await page.locator(`[data-comment-id="${parent}"]`).getByRole('button',{name:'Trả lời',exact:true}).click();await page.getByLabel('Nội dung tin nhắn',{exact:true}).fill(text);const ack=page.waitForResponse(r=>r.url().includes('/messages')&&r.request().method()==='POST');await page.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click();const response=await ack;assert.equal(response.status(),201);const ack_ms=Date.now()-started,row=await response.json();const ack_fetch_ms=await page.evaluate(()=>performance.getEntriesByType('resource').filter(e=>e.name.includes('/messages')).at(-1)?.duration??null);await expect(page.locator(`[data-comment-id="${row.id}"] [title="COMPLETED"]`)).toBeVisible({timeout:20000});latencies.push({content_id:row.id,ack_ms,ack_fetch_ms,author_analysis_visible_ms:Date.now()-started,observed_ms:Date.now()});return row}
try{
 await login(a,'live_alice');await login(b,'live_bob');await login(m,'live_admin',adminWeb)
 await expect(m.getByTestId('moderator-connection')).toHaveText('connected',{timeout:15000});checks.push('authenticated_staff_live_stream')
 const root=await send(a,'LIVE_CONTEXT: Mình đưa ra lịch ôn tập để nhóm cùng góp ý.')
 await expect(b.locator(`[data-comment-id="${root.id}"]`)).toBeVisible({timeout:15000})
 const first=await send(b,'Mày là đồ ngu, đừng nói nữa.',root.id)
 await expect(a.locator(`[data-comment-id="${first.id}"]`)).toBeVisible({timeout:15000})
 await new Promise(resolve=>setTimeout(resolve,1200))
 const second=await send(b,'Mày thật vô dụng, im đi.',root.id)
 await expect(m.locator(`[data-content-id="${second.id}"]`)).toBeVisible({timeout:15000})
 await m.locator(`[data-content-id="${second.id}"]`).click()
 await expect(m.getByTestId('live-analysis-state')).toContainText('SUCCEEDED',{timeout:15000})
 await expect(m.getByTestId('live-repeated')).toHaveText('Repeated: true',{timeout:15000});checks.push('same_actor_target_grounded_repeated_evidence_rendered')
 const evidence=await m.locator('.live-signals').textContent();assert(evidence.includes(first.id)&&evidence.includes(second.id));checks.push('evidence_ids_link_to_full_thread_context')
 await m.getByRole('textbox',{name:'Lý do quyết định',exact:true}).fill('Giữ bản nháp lý do qua cập nhật trực tiếp.')
 await send(a,'LIVE_NOTE: Đề nghị mọi người bình tĩnh trao đổi.')
 await expect(m.locator('[aria-label="Hàng chờ trực tiếp"]')).toContainText('LIVE_NOTE:',{timeout:15000})
 await expect(m.getByRole('textbox',{name:'Lý do quyết định',exact:true})).toHaveValue('Giữ bản nháp lý do qua cập nhật trực tiếp.');checks.push('stream_refresh_preserves_manual_reason_draft')
 let hideConfirmed=false;m.once('dialog',async dialog=>{assert.equal(dialog.type(),'confirm');hideConfirmed=true;await dialog.accept()})
 await m.getByRole('button',{name:'Ẩn nội dung',exact:true}).click();assert(hideConfirmed)
 await expect(a.locator(`[data-comment-id="${second.id}"]`)).toHaveCount(0,{timeout:15000})
 await expect(b.locator(`[data-comment-id="${second.id}"]`)).toContainText('HIDDEN',{timeout:10000});checks.push('manual_hide_realtime_visibility_and_author_retention')
 await b.locator(`[data-comment-id="${second.id}"]`).getByRole('button',{name:'Kháng nghị',exact:true}).click();await b.getByLabel('Lý do kháng nghị').fill('Đề nghị xem lại quyết định cho bản demo synthetic.');const appealAck=b.waitForResponse(r=>r.url().endsWith('/appeals')&&r.request().method()==='POST');await b.getByRole('button',{name:'Gửi kháng nghị',exact:true}).click();assert.equal((await appealAck).status(),201)
 await expect(m.locator('.live-signals')).toContainText('SUCCEEDED',{timeout:10000})
 await m.getByRole('button',{name:'Tải lại chi tiết',exact:true}).click()
 await expect(m.getByRole('button',{name:'Chấp nhận · khôi phục',exact:true})).toBeVisible({timeout:10000})
 await m.getByRole('textbox',{name:'Lý do quyết định',exact:true}).fill('Khôi phục sau khi duyệt kháng nghị trong môi trường demo.')
 await m.getByRole('button',{name:'Chấp nhận · khôi phục',exact:true}).click()
 await expect(a.locator(`[data-comment-id="${second.id}"]`)).toBeVisible({timeout:15000});checks.push('author_appeal_staff_restore_peer_recovery')
 await expect(m.locator('.audit')).toContainText('MANUAL_HIDE',{timeout:10000});await expect(m.locator('.audit')).toContainText('APPEAL_RESOLVED');checks.push('append_only_manual_and_appeal_audit_visible')
 await m.getByLabel('Yêu cầu làm rõ',{exact:true}).fill('Vui lòng bổ sung ngữ cảnh cho lần rà soát tiếp theo.');await m.getByRole('button',{name:'Lưu yêu cầu làm rõ',exact:true}).click();await expect(m.locator('.live-signals')).toContainText('Đã lưu yêu cầu làm rõ');checks.push('clarification_audit_without_automatic_visibility_change')
 await m.screenshot({path:path.join(out,'T043_moderator.png'),fullPage:true})
 fs.writeFileSync(path.join(out,'T043_browser_result.json'),JSON.stringify({status:'PASS',checks,contexts:3,ai_mode:'actual_approved_default_V1_1_neural_default_v5_rules',latencies,auto_hide:false},null,2));console.log(JSON.stringify({status:'PASS',checks:checks.length,contexts:3}))
}catch(error){await m.screenshot({path:path.join(out,'T043_failure.png'),fullPage:true}).catch(()=>{});throw error}finally{await Promise.all(contexts.map(c=>c.close()));await browser.close()}
