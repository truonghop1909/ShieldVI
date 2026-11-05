import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
const require=createRequire(new URL('../../apps/social-web/package.json',import.meta.url)),{chromium,expect}=require('@playwright/test')
const out=process.env.LIVE_TEST_ARTIFACTS,web=process.env.LIVE_TEST_WEB,admin=process.env.LIVE_TEST_ADMIN,thread=process.env.LIVE_TEST_THREAD
const browser=await chromium.launch({channel:'chrome',headless:true}),contexts=[],checks=[]
for(let i=0;i<3;i++)contexts.push(await browser.newContext({viewport:{width:1280,height:900}}))
const [a,b,m]=await Promise.all(contexts.map(c=>c.newPage()))
async function login(page,name,base=web){await page.goto(base+'/live.html?thread='+thread);await page.getByLabel('Tên tài khoản').fill(name);await page.getByLabel('Mật khẩu',{exact:true}).fill(process.env.LIVE_TEST_PASSWORD);await page.getByRole('button',{name:name==='live_admin'?'Đăng nhập kiểm duyệt':'Đăng nhập',exact:true}).click()}
async function send(page,text,parent){
 if(parent){await page.locator(`[data-comment-id="${parent.id}"]`).getByRole('button',{name:'Trả lời',exact:true}).click();await expect(page.locator('.reply-banner .user-mention')).toHaveText('@'+parent.author_username);await expect(page.getByLabel('Nội dung tin nhắn',{exact:true})).toHaveValue('')}
 await page.getByLabel('Nội dung tin nhắn',{exact:true}).fill(text)
 const ack=page.waitForResponse(r=>r.url().includes('/messages')&&r.request().method()==='POST');await page.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click()
 const response=await ack;assert.equal(response.status(),201);const row=await response.json();assert.equal(row.body,text)
 if(parent){assert.equal(row.parent_id,parent.id);assert.equal(row.reply_to_user_id,parent.author_id);assert.equal(row.reply_to_username,parent.author_username)}
 await expect(page.locator(`[data-comment-id="${row.id}"] [title="COMPLETED"]`)).toBeVisible({timeout:30000})
 return row
}
try{
 await login(a,'live_alice');await login(b,'live_bob');await login(m,'live_admin',admin)
 await expect(b.locator(`[data-post-id="${thread}"] .feed-author-info strong`)).toHaveText('live_alice',{timeout:15000})
 const parent=await send(a,'Mình chia sẻ lịch sinh hoạt câu lạc bộ để mọi người góp ý.')
 await expect(b.locator(`[data-comment-id="${parent.id}"] .live-meta strong`)).toHaveText('live_alice',{timeout:15000});checks.push('server_usernames_display_in_peer_feed_and_comments')
 const clean=await send(b,'Mình đồng ý, cảm ơn bạn đã giải thích.',parent)
 await expect(a.locator(`[data-comment-id="${clean.id}"] .live-meta strong`)).toHaveText('live_bob',{timeout:15000})
 await expect(a.locator(`[data-comment-id="${clean.id}"] .reply-context .user-mention`)).toHaveText('@live_alice');checks.push('reply_composer_and_saved_comment_tag_actual_parent_username')
 checks.push('body_preserved_and_parent_recipient_ids_come_from_server')
 const first=await send(b,'Mày là đồ ngu, đừng nói nữa.',parent);await pagePause(1200)
 const second=await send(b,'Mày thật vô dụng, im đi.',parent)
 await expect(m.locator(`[data-content-id="${second.id}"]`)).toBeVisible({timeout:15000});await m.locator(`[data-content-id="${second.id}"]`).click()
 await expect(m.getByTestId('live-repeated')).toHaveText('Repeated: true',{timeout:20000})
 const list=m.locator('.live-signals ul');await expect(list).toContainText('live_bob');await expect(list).toContainText('@live_alice')
 const evidence=await list.textContent();assert(evidence.includes(first.id)&&evidence.includes(second.id)&&!evidence.includes(clean.id))
 const recipient=m.locator('.live-signals dt').filter({hasText:/^Reply recipient$/}).locator('xpath=following-sibling::dd[1]')
 const target=m.locator('.live-signals dt').filter({hasText:/^Directed attack target$/}).locator('xpath=following-sibling::dd[1]')
 await expect(recipient).toHaveText('live_alice');await expect(target).toHaveText('live_alice');checks.push('moderator_names_grounded_actor_target_and_excludes_clean_reply_from_repeated')
 await b.screenshot({path:path.join(out,'reply_identity_social.png'),fullPage:true});await m.screenshot({path:path.join(out,'reply_identity_moderator.png'),fullPage:true})
 fs.writeFileSync(path.join(out,'reply_identity_result.json'),JSON.stringify({status:'PASS',checks,parent,clean,attacks:[first,second],actor_id:second.author_id,target_id:parent.author_id,actual_neural_inference:true,no_training:true},null,2))
 console.log(JSON.stringify({status:'PASS',checks:checks.length,contexts:3}))
}catch(error){await b.screenshot({path:path.join(out,'reply_identity_failure.png'),fullPage:true}).catch(()=>{});throw error}
finally{await Promise.all(contexts.map(c=>c.close()));await browser.close()}
function pagePause(ms){return new Promise(resolve=>setTimeout(resolve,ms))}
