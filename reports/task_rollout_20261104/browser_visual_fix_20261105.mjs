import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
const require=createRequire(new URL('../../apps/social-web/package.json',import.meta.url)),{expect}=require('@playwright/test')
const sizes=[[320,700],[360,780],[375,812],[390,844],[768,1024],[850,700],[1024,768],[1366,768],[1650,900],[1920,1080]]

async function session(page){const cdp=await page.context().newCDPSession(page);return {page,cdp,window:(await cdp.send('Browser.getWindowForTarget')).windowId}}
async function fullScreenshot(sess,file){
 await sess.page.evaluate(()=>scrollTo({top:0,behavior:'instant'}))
 const original=await sess.page.evaluate(()=>({root:document.getElementById('root').getBoundingClientRect().width,hasGutter:innerWidth>document.documentElement.clientWidth}))
 // Hold the already-present gutter while Chrome captures beyond the viewport;
 // capture would otherwise hide the vertical scrollbar and widen fluid cards.
 const gutter=original.hasGutter?await sess.page.addStyleTag({content:'html{scrollbar-gutter:stable!important}'}):null
 const size=await sess.page.evaluate(()=>({width:innerWidth,height:Math.max(innerHeight,document.documentElement.scrollHeight),root:document.getElementById('root').getBoundingClientRect().width}))
 assert.equal(size.root,original.root,'capture gutter must not alter original DOM width')
 // Playwright's null-viewport fullPage path clips at clientWidth (excluding the
 // scrollbar) while the page can expand during capture. Capture the real CSS
 // viewport width without resizing/reflowing the document instead.
 const result=await sess.cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:true,clip:{x:0,y:0,width:size.width,height:size.height,scale:1}})
 const bytes=Buffer.from(result.data,'base64');assert.equal(bytes.readUInt32BE(16),size.width);fs.writeFileSync(file,bytes)
 const after=await sess.page.evaluate(()=>({width:innerWidth,root:document.getElementById('root').getBoundingClientRect().width}))
 assert.equal(after.width,size.width);assert.equal(after.root,size.root)
 if(gutter)await gutter.evaluate(e=>e.remove());await sess.page.waitForTimeout(30)
 assert.equal(await sess.page.evaluate(()=>document.getElementById('root').getBoundingClientRect().width),original.root)
}
async function nativeSize(s,width,height){
 await s.cdp.send('Emulation.clearDeviceMetricsOverride')
 await s.cdp.send('Browser.setWindowBounds',{windowId:s.window,bounds:{windowState:'normal'}})
 for(let attempt=0;attempt<3;attempt++){
  const value=await s.page.evaluate(()=>({width:innerWidth,height:innerHeight})),{bounds}=await s.cdp.send('Browser.getWindowBounds',{windowId:s.window})
  await s.cdp.send('Browser.setWindowBounds',{windowId:s.window,bounds:{width:Math.max(500,Math.round(bounds.width+width-value.width)),height:Math.max(400,Math.round(bounds.height+height-value.height))}})
  await s.page.waitForTimeout(100)
  if(await s.page.evaluate(([w,h])=>innerWidth===w&&innerHeight===h,[width,height]))return 'native_window'
 }
 // Windows on this host caps the outer height at 1100px (1005px content).
 // A zero width override keeps width native while supplying the requested
 // height. A separate real-window probe verifies width continues to resize.
 const actual=await s.page.evaluate(()=>({width:innerWidth,height:innerHeight}))
 if(actual.width===width&&actual.height!==height){await s.cdp.send('Emulation.setDeviceMetricsOverride',{width:0,height,deviceScaleFactor:0,mobile:false});return 'native_window_width_height_only_emulation'}
 return 'native_window'
}
async function geometry(page,shell){return page.evaluate(shell=>{
 const visible=e=>!!e.getClientRects().length&&!e.closest('[hidden]')&&getComputedStyle(e).visibility!=='hidden'
 const box=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {x:r.x,right:r.right,width:r.width,clientWidth:e.clientWidth,scrollWidth:e.scrollWidth,display:s.display,widthRule:s.width,maxWidth:s.maxWidth,minWidth:s.minWidth,grid:s.gridTemplateColumns,overflowX:s.overflowX}}
 const selectors=['html','body','#root',shell,`${shell}>header`,'.live-layout','.live-content','.live-nav','.live-filters','.live-desk','.queue-list','.live-detail','.quick-ai-grid','.studio-import','.annotation-grid','.annotation-controls','.studio-training-options','.responsive-table']
 const containers=Object.fromEntries(selectors.map(q=>[q,document.querySelector(q)]).filter(([,e])=>e&&visible(e)).map(([q,e])=>[q,box(e)]))
 const fields=[...document.querySelectorAll('input:not([type=checkbox]):not([type=radio]),select,textarea,button')].filter(visible).map(e=>{
  const r=e.getBoundingClientRect();let parent=e.parentElement,clipped=false
  while(parent&&parent!==document.body){const s=getComputedStyle(parent),p=parent.getBoundingClientRect();if(['auto','scroll','hidden','clip'].includes(s.overflowX)&&(r.x<p.x-2||r.right>p.right+2))clipped=true;parent=parent.parentElement}
  return {name:(e.labels?.[0]?.textContent||e.getAttribute('aria-label')||e.textContent||e.tagName).trim().slice(0,90),x:r.x,right:r.right,width:r.width,height:r.height,clipped,outside:r.x< -2||r.right>document.documentElement.clientWidth+2}
 })
 return {innerWidth,innerHeight,outerWidth,outerHeight,dpr:devicePixelRatio,clientWidth:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,visualViewport:visualViewport.width,containers,fields,responsiveLoaded:getComputedStyle(document.documentElement).getPropertyValue('--ui-brand').trim(),stylesheets:[...document.querySelectorAll('style[data-vite-dev-id]')].map(s=>s.dataset.viteDevId),resourceStyles:performance.getEntriesByType('resource').filter(e=>/responsive.*css/.test(e.name)).map(e=>new URL(e.name).pathname)}
},shell)}
function violations(m,shell,width){
 const problems=[],root=m.containers['#root'],app=m.containers[shell],available=m.clientWidth
 if(m.innerWidth!==width)problems.push('native_viewport_does_not_follow_window')
 if(!root||root.width<available*.98)problems.push('root_does_not_fill_viewport')
 if(!app||app.width<available*.96)problems.push('app_shell_too_narrow')
 if(app&&Math.abs(app.x-(available-app.right))>4)problems.push('app_shell_not_centered')
 if(m.scrollWidth>available+2)problems.push('horizontal_page_overflow')
 if(m.fields.some(f=>f.outside||f.clipped))problems.push('field_outside_or_clipped')
 if(!m.responsiveLoaded)problems.push('responsive_css_not_loaded')
 if(width>=1440&&shell==='.live-admin'){
  const desk=m.containers['.live-desk'];if(!desk||desk.width<available*.92)problems.push('moderator_workspace_underuses_desktop')
 }
 if(width>=768&&width<=1023&&m.containers['.live-filters']){
  if(m.containers['.live-filters'].grid.split(' ').length>2)problems.push('tablet_filters_too_many_columns')
  const target=m.fields.find(f=>f.name==='Thread trong trang');if(!target||target.width<160||target.outside||target.clipped)problems.push('thread_filter_not_fully_available')
 }
 return problems
}
export async function runVisualChecks(pages,browser,out,{audit=false}={}){
 const [a,b,m,s]=pages.length===4?pages:[pages[0],pages[1],pages[5],pages[6]],records=[],probes=[],checks=[],errors=[]
 const lifecycle=value=>fs.appendFileSync(path.join(out,'visual_browser_lifecycle.jsonl'),JSON.stringify({at:Date.now(),...value})+'\n')
 browser.on('disconnected',()=>lifecycle({event:'browser_disconnected'}))
 for(const [index,p] of pages.entries())p.on('close',()=>lifecycle({event:'page_closed',index}))
 for(const p of [a,b,m,s])p.on('pageerror',e=>errors.push(e.message))
 const sessions=new Map();for(const p of [a,m,s])sessions.set(p,await session(p))
 const save=()=>fs.writeFileSync(path.join(out,'visual_result.json'),JSON.stringify({status:audit?'AUDIT':'IN_PROGRESS',audit,checks,records,native_probes:probes,page_errors:errors,sizes},null,2))
 async function send(p,text,parent){if(parent)await p.locator(`[data-comment-id="${parent.id}"]`).getByRole('button',{name:'Trả lời',exact:true}).click();await p.getByLabel('Nội dung tin nhắn',{exact:true}).fill(text);const done=p.waitForResponse(r=>r.url().endsWith('/messages')&&r.request().method()==='POST');await p.getByRole('button',{name:'Gửi tin nhắn',exact:true}).click();const response=await done;assert.equal(response.status(),201);return response.json()}
 async function capture(p,route,shell){
  const sess=sessions.get(p)
  // Native desktop resizing comes first; phone sizes require explicit emulation
  // because Chrome enforces a minimum width on physical desktop windows.
  for(const [width,height] of [...sizes.filter(([w])=>w>=768),...sizes.filter(([w])=>w<768)]){
   let mode='native_window'
   if(audit){mode='explicit_viewport_emulation';await p.setViewportSize({width,height})}
   else if(width<768){mode='explicit_mobile_metrics';await sess.cdp.send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:false,screenWidth:width,screenHeight:height})}
   else mode=await nativeSize(sess,width,height)
   await p.waitForTimeout(100);const metrics=await geometry(p,shell),problems=violations(metrics,shell,width)
   records.push({route,requested:{width,height},mode,metrics,problems});save()
   await fullScreenshot(sess,path.join(out,`${audit?'before':'after'}_${route}_${width}.png`))
   if(!audit){assert.equal(metrics.innerHeight,height,`${route}/${width} height`);assert.deepEqual(problems,[],`${route}/${width}: ${JSON.stringify(problems)} ${JSON.stringify(metrics.fields.filter(f=>f.outside||f.clipped))}`)}
  }
 }
 try{
  await expect(a.getByTestId('live-connection')).toHaveText('Đã kết nối trực tiếp',{timeout:20000});await expect(b.getByTestId('live-connection')).toHaveText('Đã kết nối trực tiếp',{timeout:20000})
  const root=await send(a,'Lịch làm việc nhóm: thứ bảy cùng chuẩn bị triển lãm ảnh.\n'+('Mọi người góp ý giúp mình về thời gian và địa điểm nhé. '.repeat(6))+'https://example.org/'+('hinhanh'.repeat(22)))
  await expect(b.locator(`[data-comment-id="${root.id}"]`)).toHaveCount(1,{timeout:20000});const reply=await send(b,'Mình mang bảng hướng dẫn và giá đỡ tới.',root)
  await expect(a.locator(`[data-comment-id="${reply.id}"]`)).toHaveCount(1,{timeout:20000});const third=await send(a,'Cảm ơn, mình sẽ đến sớm để hỗ trợ.',reply)
  await expect(b.locator(`[data-comment-id="${third.id}"]`)).toHaveCount(1,{timeout:20000});const attack=await send(b,'Mày là đồ ngu, đừng nói nữa.',third)
  await expect(m.locator(`[data-content-id="${attack.id}"]`)).toBeVisible({timeout:20000});await m.locator(`[data-content-id="${attack.id}"]`).click();await expect(m.getByTestId('live-analysis-state')).toContainText('SUCCEEDED',{timeout:30000});checks.push('populated_real_demo_database_two_accounts_nested_replies_actual_ai_warning')
  // Preserve the genuine launch state for root-cause evidence, before any
  // page.setViewportSize() call changes Playwright's fixed viewport.
  for(const [p,name,shell] of [[a,'social','.live-app'],[m,'moderator','.live-admin'],[s,'studio','.studio-app']]){
   const sess=sessions.get(p)
   for(const width of [1650,850]){
    await sess.cdp.send('Browser.setWindowBounds',{windowId:sess.window,bounds:{windowState:'normal'}})
    await sess.cdp.send('Browser.setWindowBounds',{windowId:sess.window,bounds:{width,height:900}});await p.waitForTimeout(150)
    const {bounds}=await sess.cdp.send('Browser.getWindowBounds',{windowId:sess.window}),metrics=await geometry(p,shell)
    probes.push({route:name,browser_window_bounds:bounds,metrics});save();await fullScreenshot(sess,path.join(out,`${audit?'before':'after'}_native_probe_${name}_${width}.png`))
   }
  }
  await capture(a,'social_feed_detail','.live-app');await capture(m,'moderator_review','.live-admin')
  await m.getByRole('button',{name:'Test AI bằng JSON',exact:true}).click();await m.getByRole('button',{name:'Nạp JSON mẫu',exact:true}).click();await m.getByRole('button',{name:'Phân tích hội thoại',exact:true}).click();await expect(m.getByTestId('quick-test-status')).toHaveText('Hoàn tất · 5/5 bình luận',{timeout:90000});await capture(m,'json_results','.quick-ai');checks.push('actual_json_inference_and_complete_signal_cards')
  const rows=[{thread_id:'VISUAL_FIX_SYNTHETIC',comment_id:'c1',parent_id:null,user_id:'A',timestamp:'2026-11-05T00:00:00Z',text:'Mình chuẩn bị bảng hướng dẫn cho buổi triển lãm nhé. '+('https://example.org/'+('chitiet'.repeat(20)))},{thread_id:'VISUAL_FIX_SYNTHETIC',comment_id:'c2',parent_id:'c1',user_id:'B',timestamp:'2026-11-05T00:01:00Z',text:'Mình mang giá đỡ đến cổng câu lạc bộ.'}]
  await s.getByLabel('File dataset (UTF-8, tối đa 1 MiB)').setInputFiles({name:'visual_synthetic.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(rows))});await s.getByRole('combobox',{name:'Loại dataset',exact:true}).selectOption('UNLABELED');await s.getByRole('button',{name:'Kiểm tra và tạo phiên bản',exact:true}).click();await expect(s.getByTestId('dataset-result')).toContainText('ACCEPTED',{timeout:30000});await capture(s,'datasets','.studio-app');checks.push('real_isolated_dataset_file_upload_and_preview')
  await s.getByRole('button',{name:'Mở Labeling',exact:true}).click();await s.getByRole('button',{name:'Gán nhãn c2',exact:true}).click();await s.getByRole('button',{name:'CLEAN',exact:true}).click();await expect(s.getByTestId('annotation-save')).toContainText('Đã lưu',{timeout:15000});await capture(s,'annotation','.studio-app');checks.push('synthetic_ui_annotation_draft_not_human_gold')
  await s.getByRole('button',{name:'Training',exact:true}).click();await s.locator('.studio-choices input[type="checkbox"]').first().check();await s.getByRole('spinbutton',{name:'Epochs',exact:true}).fill('2');await capture(s,'training_config','.studio-app');await expect(s.getByRole('spinbutton',{name:'Epochs',exact:true})).toHaveValue('2');checks.push('training_config_touch_selection_and_resize_no_training_started')
  await s.getByRole('button',{name:'Models & Evaluation',exact:true}).click();await expect(s.locator('table')).toHaveCount(1,{timeout:15000});await s.locator('.studio-choices input[type="checkbox"]').nth(0).check();await s.locator('.studio-choices input[type="checkbox"]').nth(1).check();await capture(s,'evaluation','.studio-app');checks.push('real_registry_models_and_touch_selection_no_evaluation_started')
  if(!audit){
   await nativeSize(sessions.get(m),1650,900)
   const narrow=await m.addStyleTag({content:'#root{width:1075px!important;margin-left:0!important;margin-right:0!important}'}),bad=await geometry(m,'.quick-ai')
   assert(violations(bad,'.quick-ai',1650).includes('root_does_not_fill_viewport'));await narrow.evaluate(e=>e.remove());checks.push('negative_control_rejects_1075px_left_aligned_root_at_1650')
   await m.getByRole('button',{name:'Hàng chờ realtime',exact:true}).click();await nativeSize(sessions.get(m),850,700)
   const cut=await m.addStyleTag({content:'.live-filters{grid-template-columns:repeat(3,400px)!important}'}),cutMetrics=await geometry(m,'.live-admin')
   assert(violations(cutMetrics,'.live-admin',850).includes('field_outside_or_clipped'));await cut.evaluate(e=>e.remove());checks.push('negative_control_rejects_clipped_tablet_filters')
   const field=m.getByRole('textbox',{name:'Thread trong trang',exact:true});await field.fill('test-thread-filter');await expect(field).toHaveValue('test-thread-filter');await field.fill('');checks.push('thread_filter_editable_at_native_850px')
   await a.getByLabel('Nội dung tin nhắn',{exact:true}).fill('Giữ bản nháp qua cập nhật realtime.');await send(b,'Mình bổ sung sơ đồ khu trưng bày.');await expect(a.getByLabel('Nội dung tin nhắn',{exact:true})).toHaveValue('Giữ bản nháp qua cập nhật realtime.');checks.push('peer_realtime_does_not_discard_mobile_draft')
  }
  assert.equal(errors.length,0,errors.join('\n'));save()
  const result=JSON.parse(fs.readFileSync(path.join(out,'visual_result.json'),'utf8'));result.status=audit?'AUDIT':'PASS';result.scope='actual_headed_script_demo_native_desktop_and_explicit_mobile_emulation';result.training_started=false;result.evaluation_started=false;fs.writeFileSync(path.join(out,'visual_result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({status:result.status,measurements:records.length,violations:records.filter(r=>r.problems.length).length,checks:checks.length}))
  // Leave the user's new demo on useful desktop pages.
  if(!audit){await nativeSize(sessions.get(a),1650,900);await nativeSize(sessions.get(m),1650,900);await nativeSize(sessions.get(s),1650,900);await s.getByRole('button',{name:'Datasets',exact:true}).click()}
 }catch(error){save();throw error}
}
