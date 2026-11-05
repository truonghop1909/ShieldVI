import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import {configureDemoDownloads} from '../../scripts/demo_downloads.mjs'
const require=createRequire(new URL('../../apps/social-web/package.json',import.meta.url)),{chromium,expect}=require('@playwright/test')
const out=process.env.LIVE_TEST_ARTIFACTS,browser=await chromium.launch({channel:'chrome',headless:false}),context=await browser.newContext({viewport:null}),page=await context.newPage(),checks=[]
const folder=await configureDemoDownloads(context,page,out)
try{
 await page.goto(process.env.LIVE_TEST_ADMIN+'/live.html');await page.getByLabel('Tên tài khoản',{exact:true}).fill('live_admin');await page.getByLabel('Mật khẩu',{exact:true}).fill(process.env.LIVE_TEST_PASSWORD);await page.getByRole('button',{name:'Đăng nhập kiểm duyệt',exact:true}).click()
 await page.getByRole('button',{name:'Test AI bằng JSON',exact:true}).click();await page.getByRole('button',{name:'Nạp JSON mẫu',exact:true}).click();const sample=JSON.parse(await page.getByLabel('JSON hội thoại',{exact:true}).inputValue())
 await page.getByRole('button',{name:'Phân tích hội thoại',exact:true}).click();await expect(page.getByTestId('quick-test-status')).toHaveText('Hoàn tất · 5/5 bình luận',{timeout:90000});checks.push('real_staff_quick_json_inference_completed')
 const event=page.waitForEvent('download');await page.getByRole('button',{name:'Tải kết quả JSON',exact:true}).click();const download=await event,filename=download.suggestedFilename()
 assert(filename.startsWith(sample.thread_id.replace(/[^A-Za-z0-9_-]/g,'_')+'_analysis_'));assert.match(filename,/_\d{8}_\d{6}_\d{3}_[a-f0-9]{16}\.json$/)
 const type=await page.evaluate(async url=>(await fetch(url)).headers.get('content-type'),download.url());assert(type.startsWith('application/json'))
 const file=path.join(folder,filename);await expect.poll(()=>fs.existsSync(file),{timeout:10000}).toBe(true)
 const result=JSON.parse(fs.readFileSync(file,'utf8'));assert.equal(result.thread_id,sample.thread_id);assert.equal(result.comments.length,5);assert.deepEqual(result.comments.map(c=>c.text),sample.comments.map(c=>c.text));assert.equal(result.threshold,.41);assert.equal(result.processor,'default-v5');assert.equal(result.training_performed,false);checks.push('native_saved_file_json_extension_utf8_valid_original_text_and_separate_analysis_layers')
 const ui=await context.newPage();await ui.goto('chrome://downloads/');await expect(ui.getByRole('link',{name:filename,exact:true})).toBeVisible();await ui.screenshot({path:path.join(out,'native_json_download_chrome.png')});checks.push('chrome_downloads_ui_has_actual_json_filename_not_uuid')
 const second=page.waitForEvent('download');await page.getByRole('button',{name:'Tải kết quả JSON',exact:true}).click();await second;await expect.poll(()=>fs.readdirSync(folder).filter(f=>f.endsWith('.json')).length).toBe(2);for(const name of fs.readdirSync(folder))assert.deepEqual(JSON.parse(fs.readFileSync(path.join(folder,name),'utf8')),result);checks.push('second_export_keeps_first_file_and_identical_payload')
 await context.close();assert(fs.existsSync(file));checks.push('export_survives_demo_browser_close')
 fs.writeFileSync(path.join(out,'native_json_download_result.json'),JSON.stringify({status:'PASS',checks,files:fs.readdirSync(folder),content_type:type,actual_neural_inference:true,training_started:false},null,2));console.log(JSON.stringify({status:'PASS',checks:checks.length,files:fs.readdirSync(folder)}))
}finally{await browser.close()}
