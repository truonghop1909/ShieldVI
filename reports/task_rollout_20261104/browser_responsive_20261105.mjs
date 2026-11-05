import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
const require=createRequire(new URL('../../apps/social-web/package.json',import.meta.url)),{chromium,expect}=require('@playwright/test')
const out=process.env.LIVE_TEST_ARTIFACTS,web=process.env.LIVE_TEST_WEB,admin=process.env.LIVE_TEST_ADMIN,thread=process.env.LIVE_TEST_THREAD,before=process.env.SHIELDVI_RESPONSIVE_BEFORE==='1'
const viewports=[[320,700],[375,812],[390,844],[768,1024],[1024,768],[1366,768],[1440,900],[1920,1080],[360,780],[600,900],[820,1000],[1180,800]]
const browser=await chromium.launch({channel:'chrome',headless:true}),contexts=[],checks=[],measurements=[],errors=[]
async function page(){const c=await browser.newContext({viewport:{width:390,height:844}});contexts.push(c);const p=await c.newPage();p.on('pageerror',e=>errors.push(e.message));return p}
async function login(p,url,username,button){await p.goto(url);await p.getByLabel('Tên tài khoản',{exact:true}).fill(username);await p.getByLabel('Mật khẩu',{exact:true}).fill(process.env.LIVE_TEST_PASSWORD);await p.getByRole('button',{name:button,exact:true}).click()}
async function audit(p,route){
 for(const [width,height] of viewports){await p.setViewportSize({width,height});await p.waitForTimeout(70)
  const info=await p.evaluate(()=>{
   const visible=e=>e.getClientRects().length&&!e.closest('[hidden]')&&getComputedStyle(e).visibility!=='hidden'
   const outside=[...document.querySelectorAll('body *')].filter(e=>visible(e)&&e.getBoundingClientRect().right>innerWidth+2&&!e.closest('pre,.quick-ai-table,.responsive-table')).slice(0,8).map(e=>({tag:e.tagName,cls:e.className,right:Math.round(e.getBoundingClientRect().right)}))
   const small=[...document.querySelectorAll('button,input:not([type=checkbox]):not([type=radio]),select,summary')].filter(e=>visible(e)&&!e.disabled&&e.getBoundingClientRect().height<43).map(e=>(e.textContent||e.getAttribute('aria-label')||e.tagName).slice(0,70))
   return {overflow:document.documentElement.scrollWidth>innerWidth+2,outside,smallControls:small}
  });measurements.push({route,width,height,...info})
  if([320,390,768,1366,1920].includes(width))await p.screenshot({path:path.join(out,`${before?'before':'after'}_${route}_${width}.png`),fullPage:true})
  if(!before){assert.equal(info.overflow,false,`${route} overflow at ${width}: ${JSON.stringify(info.outside)}`);assert.equal(info.smallControls.length,0,`${route} small touch controls at ${width}: ${info.smallControls}`)}
 }
}
async function send(p,text,parent){if(parent)await p.locator(`[data-comment-id="${parent.id}"]`).getByRole('button',{name:'Trả lời',exact:true}).click();await p.getByLabel('Nội dung tin nhắn',{exact:true}).fill(text);const response=p.waitForResponse(r=>r.url().endsWith('/messages')&&r.request().method()==='POST');await p.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click();const result=await (await response).json();assert(result.id);return result}
try{
 const a=await page(),b=await page(),m=await page(),s=await page()
 await a.goto(web+'/live.html');await audit(a,'social_login')
 await m.goto(admin+'/live.html');await audit(m,'moderator_login')
 await s.goto(admin+'/studio.html');await audit(s,'studio_login')
 await login(a,web+'/live.html?thread='+thread,'live_alice','Đăng nhập');await expect(a.getByTestId('live-connection')).toHaveText('Đã kết nối trực tiếp',{timeout:20000})
 await login(b,web+'/live.html?thread='+thread,'live_bob','Đăng nhập');await expect(b.getByTestId('live-connection')).toHaveText('Đã kết nối trực tiếp',{timeout:20000})
 await login(m,admin+'/live.html','live_admin','Đăng nhập kiểm duyệt');await expect(m.getByTestId('moderator-connection')).toHaveText('connected',{timeout:20000})
 await login(s,admin+'/studio.html','live_admin','Đăng nhập Studio');await expect(s.getByRole('heading',{name:'Datasets',exact:true})).toBeVisible()
 const root=await send(a,'Mình gửi lịch sinh hoạt câu lạc bộ.\n'+('Cảm ơn mọi người đã góp ý và chia sẻ thông tin. '.repeat(12))+'https://example.org/'+('duongdan'.repeat(28)))
 await expect(b.locator(`[data-comment-id="${root.id}"]`)).toHaveCount(1,{timeout:20000});const reply=await send(b,'Mình nhận được lịch rồi, cảm ơn bạn.',root)
 await expect(a.locator(`[data-comment-id="${reply.id}"]`)).toHaveCount(1,{timeout:20000});const third=await send(a,'Mình bổ sung thông tin địa điểm ở đây nhé.',reply)
 await expect(b.locator(`[data-comment-id="${third.id}"]`)).toHaveCount(1,{timeout:20000});const fourth=await send(b,'Mình sẽ đến sớm phụ mọi người.',third)
 await expect(a.locator(`[data-comment-id="${fourth.id}"] .reply-context`)).toContainText('@live_alice',{timeout:20000})
 checks.push('two_authenticated_accounts_long_multiline_content_four_level_reply_parent_tags_no_refresh')
 await a.getByLabel('Nội dung tin nhắn',{exact:true}).fill('Bản nháp trên điện thoại vẫn giữ nguyên.')
 const attack=await send(b,'Mày là đồ ngu, đừng nói nữa.',root)
 await expect(a.locator(`[data-comment-id="${attack.id}"] [title="COMPLETED"]`)).toBeVisible({timeout:30000})
 await expect(a.getByLabel('Nội dung tin nhắn',{exact:true})).toHaveValue('Bản nháp trên điện thoại vẫn giữ nguyên.')
 await audit(a,'social_feed_detail')
 await m.locator(`[data-content-id="${attack.id}"]`).click();await expect(m.getByRole('region',{name:'Chi tiết kiểm duyệt'})).toContainText(attack.body,{timeout:20000});await expect(m.getByTestId('live-analysis-state')).toContainText('SUCCEEDED',{timeout:20000})
 await audit(m,'moderator_review');checks.push('moderator_opens_real_ai_warning_context_and_review')
 await m.getByRole('button',{name:'Test AI bằng JSON',exact:true}).click();await m.getByRole('button',{name:'Nạp JSON mẫu',exact:true}).click();await audit(m,'json_test')
 if(!before){await m.getByRole('button',{name:'Phân tích hội thoại',exact:true}).click();await expect(m.getByTestId('quick-test-status')).toHaveText('Hoàn tất · 5/5 bình luận',{timeout:90000});await audit(m,'json_results');await expect(m.locator('[data-quick-comment="c03"]')).toContainText('U01');checks.push('actual_json_neural_results_mobile_cards_preserve_raw_context_policy_target_and_details')}
 const rows=[{thread_id:'RESPONSIVE_SYNTHETIC_UI',comment_id:'c1',parent_id:null,user_id:'A',timestamp:'2026-11-05T00:00:00Z',text:'Chiều nay mình cùng chuẩn bị khu triển lãm ảnh nhé. '+('https://example.org/'+('abc'.repeat(50)))},{thread_id:'RESPONSIVE_SYNTHETIC_UI',comment_id:'c2',parent_id:'c1',user_id:'B',timestamp:'2026-11-05T00:01:00Z',text:'Mình mang giá đỡ và phụ dựng bảng bên cạnh quầy đăng ký.'}]
 await s.getByLabel('File dataset (UTF-8, tối đa 1 MiB)').setInputFiles({name:'responsive_synthetic.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(rows))});await s.getByRole('combobox',{name:'Loại dataset',exact:true}).selectOption('UNLABELED');await s.getByRole('button',{name:'Kiểm tra và tạo phiên bản',exact:true}).click();await expect(s.getByTestId('dataset-result')).toContainText('ACCEPTED',{timeout:30000});await audit(s,'datasets');checks.push('actual_isolated_synthetic_file_upload_validation_and_preview')
 await s.getByRole('button',{name:'Mở Labeling',exact:true}).click();await expect(s.locator('.annotation-grid')).toContainText(rows[1].text,{timeout:15000});await s.getByRole('button',{name:'Gán nhãn c2',exact:true}).click();await s.getByRole('button',{name:'CLEAN',exact:true}).click();await expect(s.getByTestId('annotation-save')).toContainText('Đã lưu',{timeout:15000});await audit(s,'annotation');checks.push('synthetic_ui_annotation_draft_autosave_full_parent_child_context_not_human_gold')
 // Browser-only fixture for progress rendering. No training start request or worker.
 const progress={id:'RESPONSIVE_UI_FIXTURE',status:'RUNNING',error_code:null,metrics:{stage:'head_epoch',optimizer_steps:3,epoch:1,encoder_unchanged:true,epochs:[{epoch:1,mean_batch_loss:.72,validation:{macro_f1:.61}},{epoch:2,mean_batch_loss:.53,validation:{macro_f1:.68}}]},manifest:null}
 await s.route('**/training-runs',r=>r.request().method()==='GET'?r.fulfill({json:{items:[progress]}}):r.abort())
 await s.route('**/training-runs/RESPONSIVE_UI_FIXTURE',r=>r.fulfill({json:progress}));await s.route('**/training-runs/RESPONSIVE_UI_FIXTURE/logs',r=>r.fulfill({json:{text:'BROWSER UI FIXTURE ONLY — no training executed.\n'+('log_long_line_'.repeat(60))}}))
 await s.getByRole('button',{name:'Training',exact:true}).click();await s.getByRole('button',{name:'RESPONSIVE_UI_FIXTURE · RUNNING',exact:true}).click();await expect(s.getByTestId('training-status')).toHaveText('RUNNING');if(!before){await expect(s.getByRole('img',{name:'Mean batch loss',exact:true})).toBeVisible();await expect(s.getByRole('img',{name:'Validation Macro-F1',exact:true})).toBeVisible();await s.getByRole('spinbutton',{name:'Epochs',exact:true}).fill('2');await s.getByRole('spinbutton',{name:'Learning rate',exact:true}).fill('0.0001');await s.getByRole('spinbutton',{name:'Batch size',exact:true}).fill('16');await s.locator('.studio-choices input[type="checkbox"]').first().check()}await s.getByText('Worker log',{exact:true}).click();await audit(s,'training_progress');if(!before){await expect(s.getByRole('spinbutton',{name:'Epochs',exact:true})).toHaveValue('2');await expect(s.locator('.studio-choices input:checked')).toHaveCount(1);checks.push('touch_dataset_choice_and_training_config_retained_across_resize_without_start')}checks.push('training_config_progress_logs_browser_fixture_only_no_training')
 await s.getByRole('button',{name:'Models & Evaluation',exact:true}).click();await expect(s.locator('table')).toHaveCount(1,{timeout:20000});if(!before){await s.locator('.studio-choices input[type="checkbox"]').nth(0).check();await s.locator('.studio-choices input[type="checkbox"]').nth(1).check()}await audit(s,'evaluation_registry');if(!before){await expect(s.locator('.studio-choices input:checked')).toHaveCount(2);checks.push('touch_model_comparison_selection_retained_across_resize_without_evaluation_start')}
 if(!before){
  await m.getByRole('button',{name:'Hàng chờ realtime',exact:true}).click();await m.getByLabel('Lý do quyết định',{exact:true}).fill('Kiểm tra hủy xác nhận responsive synthetic UI.');let cancelSeen=false;m.once('dialog',async dialog=>{assert.equal(dialog.type(),'confirm');cancelSeen=true;await dialog.dismiss()});await m.getByRole('button',{name:'Ẩn nội dung',exact:true}).click();assert(cancelSeen);await expect(m.getByRole('button',{name:'Ẩn nội dung',exact:true})).toBeEnabled();checks.push('dangerous_hide_confirmation_cancel_preserves_content_and_review');
  await a.setViewportSize({width:320,height:700});await a.getByRole('link',{name:'Tài khoản',exact:true}).click();await expect(a.locator('#live-account')).toContainText('live_alice');await audit(a,'account')
  await s.getByRole('button',{name:'Labeling',exact:true}).click();await expect(s.locator('.annotation-grid')).toBeVisible();await s.setViewportSize({width:375,height:812});await s.getByRole('button',{name:'Gán nhãn c2',exact:true}).click();await expect(s.locator('#annotation-controls')).toHaveAttribute('open','');await s.getByRole('textbox',{name:'Ghi chú / lý do UNCERTAIN',exact:true}).fill('Responsive UI synthetic draft');await expect(s.getByTestId('annotation-save')).toContainText('Đã lưu',{timeout:15000});await s.setViewportSize({width:1366,height:768});await expect(s.getByRole('textbox',{name:'Ghi chú / lý do UNCERTAIN',exact:true})).toHaveValue('Responsive UI synthetic draft');checks.push('annotation_panel_opens_for_selected_comment_keeps_draft_across_resize')
  await b.context().setOffline(true);await expect(b.getByTestId('live-connection')).not.toHaveText('Đã kết nối trực tiếp',{timeout:20000});await b.context().setOffline(false);await expect(b.getByTestId('live-connection')).toHaveText('Đã kết nối trực tiếp',{timeout:20000});await expect(b.locator(`[data-comment-id="${root.id}"]`)).toHaveCount(1);checks.push('offline_reconnect_state_and_no_duplicate_comments')
  await a.setViewportSize({width:390,height:844});await a.getByLabel('Nội dung tin nhắn',{exact:true}).scrollIntoViewIfNeeded();await a.getByLabel('Nội dung tin nhắn',{exact:true}).focus();const scroll=await a.evaluate(()=>scrollY);await send(b,'Mình xác nhận lại thông tin mới nhất.');await expect(a.getByLabel('Nội dung tin nhắn',{exact:true})).toHaveValue('Bản nháp trên điện thoại vẫn giữ nguyên.');assert(Math.abs((await a.evaluate(()=>scrollY))-scroll)<5);checks.push('mobile_draft_and_document_scroll_stable_on_peer_realtime_update')
  await a.getByLabel('Nội dung bài đăng',{exact:true}).fill('Bài đăng từ responsive browser test.');await a.getByRole('button',{name:'Đăng bài',exact:true}).click();await expect(a.locator('.live-root')).toHaveText('Bài đăng từ responsive browser test.',{timeout:20000});checks.push('create_post_actual_api')
 }
 assert.equal(errors.length,0,errors.join('\n'))
 fs.writeFileSync(path.join(out,'responsive_result.json'),JSON.stringify({status:before?'AUDIT':'PASS',before,viewports,checks,measurements,page_errors:errors,training:'browser_progress_fixture_only_no_training',reference:'synthetic_ui_controls_not_human_gold'},null,2));console.log(JSON.stringify({status:before?'AUDIT':'PASS',checks:checks.length,layoutChecks:measurements.length,overflowCases:measurements.filter(x=>x.overflow).length}))
}catch(error){fs.writeFileSync(path.join(out,'responsive_partial.json'),JSON.stringify({checks,measurements,errors,error:String(error)},null,2));throw error}
finally{await Promise.all(contexts.map(c=>c.close()));await browser.close()}
