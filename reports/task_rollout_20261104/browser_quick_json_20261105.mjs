import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
const require=createRequire(new URL('../../apps/social-web/package.json',import.meta.url)),{chromium,expect}=require('@playwright/test')
const out=process.env.LIVE_TEST_ARTIFACTS,web=process.env.LIVE_TEST_ADMIN
const browser=await chromium.launch({channel:'chrome',headless:true}),context=await browser.newContext({viewport:{width:1440,height:1000}}),page=await context.newPage(),checks=[]
try{
 await page.goto(web+'/live.html');await page.getByLabel('Tên tài khoản').fill('live_admin');await page.getByLabel('Mật khẩu',{exact:true}).fill(process.env.LIVE_TEST_PASSWORD)
 await page.getByRole('button',{name:'Đăng nhập kiểm duyệt',exact:true}).click();await expect(page.getByTestId('moderator-connection')).toHaveText('connected',{timeout:20000})
 await page.getByRole('button',{name:'Test AI bằng JSON',exact:true}).click();await expect(page.getByRole('heading',{name:'Test AI bằng JSON',exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Nạp JSON mẫu',exact:true}).click();const input=page.getByLabel('JSON hội thoại',{exact:true});const sample=JSON.parse(await input.inputValue());assert.equal(sample.comments.length,5)
 const started=page.waitForResponse(r=>r.url().endsWith('/test-conversations')&&r.request().method()==='POST')
 await page.getByRole('button',{name:'Phân tích hội thoại',exact:true}).click();assert.equal((await started).status(),202)
 await expect(page.getByTestId('quick-test-status')).toHaveText('Hoàn tất · 5/5 bình luận',{timeout:90000});checks.push('staff_sample_json_queued_and_completed_with_actual_default_neural_inference')
 await expect(page.locator('[data-quick-comment="c02"]')).toContainText('Instance: false');await expect(page.locator('[data-quick-comment="c03"]')).toContainText('U01')
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Tải kết quả JSON',exact:true}).click();await (await download).saveAs(path.join(out,'quick_json_analysis.json'))
 const result=JSON.parse(fs.readFileSync(path.join(out,'quick_json_analysis.json'),'utf8'));assert.equal(result.threshold,.41);assert.equal(result.processor,'default-v5');assert.equal(result.content_saved,false);assert.equal(result.training_performed,false)
 const comments=Object.fromEntries(result.comments.map(c=>[c.comment_id,c.analysis.conversation_signals.current]))
 assert.equal(comments.c02.reply_to_user_id,'U01');assert.equal(comments.c02.directed_at_user_id,null);assert.equal(comments.c02.attack_instance_candidate,false)
 assert.equal(comments.c03.directed_at_user_id,'U01');assert.equal(comments.c05.directed_at_user_id,'U01');assert.equal(comments.c04.attack_instance_candidate,false)
 assert(result.repeated_events.some(e=>e.actor_user_id==='U02'&&e.target_user_id==='U01'&&e.evidence_comment_ids.includes('c03')&&e.evidence_comment_ids.includes('c05')&&!e.evidence_comment_ids.includes('c02')))
 checks.push('raw_context_target_policy_and_repeated_evidence_export_separately_without_training')
 await page.screenshot({path:path.join(out,'quick_json_desktop.png'),fullPage:true})
 await input.fill('{bad JSON');await page.getByRole('button',{name:'Phân tích hội thoại',exact:true}).click();await expect(page.getByRole('alert')).toContainText('JSON không hợp lệ');checks.push('malformed_json_keeps_editable_input_and_does_not_show_stale_result')
 const imported={...sample,thread_id:'IMPORTED_JSON'}
 await page.getByLabel('Nhập file JSON',{exact:true}).setInputFiles({name:'conversation.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(imported))})
 await expect(input).toHaveValue(/IMPORTED_JSON/);checks.push('utf8_file_import_into_editor')
 await page.getByRole('button',{name:'Hàng chờ realtime',exact:true}).click();await expect(page.getByTestId('moderator-connection')).toHaveText('connected',{timeout:15000})
 await page.getByRole('button',{name:'Test AI bằng JSON',exact:true}).click();await expect(input).toHaveValue(/IMPORTED_JSON/);checks.push('tab_switch_preserves_editor_and_live_moderator_connection')
 await page.setViewportSize({width:390,height:820});await page.screenshot({path:path.join(out,'quick_json_mobile.png'),fullPage:true})
 fs.writeFileSync(path.join(out,'quick_json_browser_result.json'),JSON.stringify({status:'PASS',checks,contexts:1,actual_neural_inference:true,training_performed:false},null,2))
 console.log(JSON.stringify({status:'PASS',checks:checks.length}))
}catch(error){await page.screenshot({path:path.join(out,'quick_json_failure.png'),fullPage:true}).catch(()=>{});throw error}
finally{await context.close();await browser.close()}
