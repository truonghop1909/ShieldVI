import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
const require=createRequire(new URL('../../apps/social-web/package.json',import.meta.url)),{expect}=require('@playwright/test')

export async function runFeedChecks(pages,out){
 const [a,b,c,d,e,m]=pages,people=[a,b,c,d,e],checks=[],latencies=[]
 const stage=value=>fs.appendFileSync(path.join(out,'feed_stages.log'),value+'\n')
 const postText='Mình chia sẻ lịch sinh hoạt câu lạc bộ, mọi người góp ý nhé. '+Date.now()
 await a.getByLabel('Nội dung bài đăng',{exact:true}).fill(postText)
 const ack=a.waitForResponse(r=>r.url().endsWith('/api/v1/posts')&&r.request().method()==='POST')
 await a.getByRole('button',{name:'Đăng bài',exact:true}).click()
 const postAck=await ack;assert.equal(postAck.status(),201);const post=await postAck.json()
 for(const person of people){const card=person.locator(`[data-post-id="${post.id}"]`);await expect(card).toContainText(postText,{timeout:30000});await card.getByRole('button',{name:'Xem bài và bình luận',exact:true}).click();await expect(person.getByTestId('live-connection')).toHaveText('Đã kết nối trực tiếp',{timeout:15000})}
 checks.push('five_real_sessions_discover_new_post_without_reload')
 async function send(page,text,parent){
  stage('Sending on '+new URL(page.url()).pathname+'; completed comments='+latencies.length)
  const start=Date.now();if(parent)await page.locator(`[data-comment-id="${parent}"]`).getByRole('button',{name:'Trả lời',exact:true}).click()
  await page.getByLabel('Nội dung tin nhắn',{exact:true}).fill(text)
  const received=page.waitForResponse(r=>r.url().includes('/messages')&&r.request().method()==='POST')
  await page.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click()
  const response=await received;assert.equal(response.status(),201);const row=await response.json(),ackMs=Date.now()-start
  await expect(page.locator(`[data-comment-id="${row.id}"] [title="COMPLETED"]`)).toBeVisible({timeout:30000})
  latencies.push({comment_id:row.id,comment_ack_ms:ackMs,author_result_visible_ms:Date.now()-start})
  return row
 }
 const root=await send(a,'Mình dự kiến sinh hoạt vào chiều thứ bảy, các bạn thấy sao?')
 for(const person of people)await expect(person.locator(`[data-comment-id="${root.id}"]`)).toBeVisible({timeout:20000})
 const rows=[root]
 for(const [index,person] of people.slice(1).entries()){
  const text=['Mình tham gia được, cảm ơn bạn đã sắp xếp.','Buổi chiều phù hợp với mình, mình sẽ mang tài liệu.','Mình có thể phụ trách phần chuẩn bị phòng học.','Mình sẽ đến sớm để hỗ trợ mọi người.'][index]
  rows.push(await send(person,text,root.id))
 }
 assert.equal(new Set(rows.map(r=>r.author_id)).size,5)
 for(const person of people)for(const row of rows)await expect(person.locator(`[data-comment-id="${row.id}"]`)).toHaveCount(1,{timeout:20000})
 checks.push('five_distinct_server_actors_comment_reply_without_reload_or_duplicates')
 const first=await send(b,'Mày là đồ ngu, đừng nói nữa.',root.id)
 await new Promise(resolve=>setTimeout(resolve,1200))
 const second=await send(b,'Mày thật vô dụng, im đi.',root.id)
 await expect(m.locator(`[data-content-id="${second.id}"]`)).toBeVisible({timeout:20000});await m.locator(`[data-content-id="${second.id}"]`).click()
 await expect(m.getByTestId('live-repeated')).toHaveText('Repeated: true',{timeout:20000})
 const evidence=await m.locator('.live-signals').textContent();assert(evidence.includes(first.id)&&evidence.includes(second.id))
 checks.push('actual_default_ai_repeated_same_actor_target_and_moderator_alert')
 await m.getByRole('textbox',{name:'Lý do quyết định',exact:true}).fill('Ẩn thủ công trong bài kiểm thử synthetic Social Feed.')
 await m.getByRole('button',{name:'Ẩn nội dung',exact:true}).click()
 await expect(a.locator(`[data-comment-id="${second.id}"]`)).toHaveCount(0,{timeout:20000})
 await expect(b.locator(`[data-comment-id="${second.id}"]`)).toContainText('HIDDEN',{timeout:20000})
 await b.locator(`[data-comment-id="${second.id}"]`).getByRole('button',{name:'Kháng nghị',exact:true}).click()
 await b.getByLabel('Lý do kháng nghị',{exact:true}).fill('Đề nghị xem lại quyết định trong dữ liệu tổng hợp.')
 await b.getByRole('button',{name:'Gửi kháng nghị',exact:true}).click()
 await m.getByRole('button',{name:'Tải lại chi tiết',exact:true}).click()
 await expect(m.getByRole('button',{name:'Chấp nhận · khôi phục',exact:true})).toBeVisible({timeout:10000})
 await m.getByRole('textbox',{name:'Lý do quyết định',exact:true}).fill('Khôi phục sau khi duyệt kháng nghị demo.')
 await m.getByRole('button',{name:'Chấp nhận · khôi phục',exact:true}).click()
 await expect(a.locator(`[data-comment-id="${second.id}"]`)).toBeVisible({timeout:20000})
 await expect(m.locator('.audit')).toContainText('APPEAL_RESOLVED',{timeout:10000})
 checks.push('manual_hide_author_appeal_restore_and_audit_without_reload')
 await b.reload();await expect(b.locator(`[data-comment-id="${root.id}"]`)).toHaveCount(1,{timeout:15000})
 checks.push('reload_retains_thread_and_no_duplicate_comments')
 const link=new URL(m.url());assert.equal(link.searchParams.get('content'),second.id);assert.equal(link.searchParams.get('kind'),'comment')
 await m.reload();await m.getByLabel('Tên tài khoản').fill('live_admin');await m.getByLabel('Mật khẩu',{exact:true}).fill(process.env.LIVE_TEST_PASSWORD);await m.getByRole('button',{name:'Đăng nhập kiểm duyệt',exact:true}).click()
 await expect(m.getByTestId('live-analysis-state')).toContainText('SUCCEEDED',{timeout:15000})
 await expect(m.locator(`#live-context-${second.id}`)).toBeVisible({timeout:15000})
 checks.push('moderator_deep_link_reauthenticates_and_opens_exact_comment_context')
 await e.context().setOffline(true);await new Promise(resolve=>setTimeout(resolve,300));await e.context().setOffline(false)
 const resumed=await send(a,'Mình xác nhận lại lịch sinh hoạt sau khi kết nối được khôi phục.')
 await expect(e.locator(`[data-comment-id="${resumed.id}"]`)).toHaveCount(1,{timeout:20000})
 checks.push('offline_reconnect_resumes_without_reload_or_duplicate')
 const xss=await send(a,'Ví dụ mã: <img src=x onerror="window.__feedXSS=1">')
 assert.equal(await a.evaluate(()=>window.__feedXSS),undefined)
 assert.equal(await a.locator(`[data-comment-id="${xss.id}"] img`).count(),0)
 checks.push('untrusted_comment_is_literal_text_not_html')
 const seeded=await a.evaluate(async postId=>{const token=sessionStorage.getItem('shieldvi-live-session'),ids=[]
  for(let i=0;i<24;i++){const response=await fetch(`/api/live/threads/${postId}/messages`,{method:'POST',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID()},body:JSON.stringify({body:`Mình bổ sung mục thảo luận số ${i+1} cho buổi sinh hoạt.`,parent_id:null})});if(!response.ok)throw Error('Long thread seed status '+response.status);ids.push((await response.json()).id)}return ids
 },post.id)
 await expect(a.locator(`[data-comment-id="${seeded.at(-1)}"] [title="COMPLETED"]`)).toBeVisible({timeout:90000})
 assert(await a.locator('[data-comment-id]').count()>=30)
 checks.push('long_thread_over_30_comments_keeps_complete_readable_items')
 const waitFile=async(name,seconds)=>{const deadline=Date.now()+seconds*1000;while(!fs.existsSync(path.join(out,name))){if(Date.now()>deadline)throw Error('Timed out waiting for owned demo '+name);await new Promise(resolve=>setTimeout(resolve,250))}}
 fs.writeFileSync(path.join(out,'ai_pause.request'),'owned demo fault injection')
 await waitFile('ai_paused.json',30)
 await a.getByLabel('Nội dung tin nhắn',{exact:true}).fill('Mình bổ sung lịch thảo luận khi dịch vụ phân tích đang khởi động lại.')
 const offlineAck=a.waitForResponse(r=>r.url().includes('/messages')&&r.request().method()==='POST')
 await a.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click();const offlineResponse=await offlineAck;assert.equal(offlineResponse.status(),201);const offline=await offlineResponse.json()
 await expect(a.locator(`[data-comment-id="${offline.id}"] .live-meta span`)).toHaveAttribute('title',/QUEUED|PROCESSING|RETRYING/,{timeout:10000})
 assert.equal(await a.locator(`[data-comment-id="${offline.id}"] [title="COMPLETED"]`).count(),0)
 fs.writeFileSync(path.join(out,'ai_resume.request'),'restart only owned AI')
 await waitFile('ai_resumed.json',100)
 await expect(a.locator(`[data-comment-id="${offline.id}"] [title="COMPLETED"]`)).toBeVisible({timeout:30000})
 await expect(e.locator(`[data-comment-id="${offline.id}"]`)).toHaveCount(1,{timeout:20000})
 checks.push('owned_ai_offline_ack_persists_retry_then_actual_recovery_without_duplicates')
 await a.screenshot({path:path.join(out,'social_feed.png'),fullPage:true});await m.screenshot({path:path.join(out,'moderator_feed.png'),fullPage:true})
 const result={status:'PASS',checks,social_accounts:5,post_id:post.id,latencies,ai_mode:'actual_approved_default_V1_1_default_v5',training_started:false}
 fs.writeFileSync(path.join(out,'social_feed_result.json'),JSON.stringify(result,null,2));return result
}
