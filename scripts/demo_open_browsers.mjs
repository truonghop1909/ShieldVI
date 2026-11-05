// Launched only by the user's interactive demo command; credentials never enter URLs.
import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import {execFile} from 'node:child_process'
import {promisify} from 'node:util'
import {configureDemoDownloads} from './demo_downloads.mjs'
const require=createRequire(new URL('../apps/social-web/package.json',import.meta.url)),{chromium,expect}=require('@playwright/test')
let browser;const pages=[]
const fail=async error=>{const root=process.env.SHIELDVI_DEMO_ROOT;fs.writeFileSync(path.join(root,'browser_failure.json'),JSON.stringify({name:error?.name||'Error',message:String(error?.stack||error).replaceAll(process.env.LIVE_TEST_PASSWORD||'__missing__','[REDACTED]')},null,2));await Promise.all(pages.map((page,index)=>page.screenshot({path:path.join(root,`failure_page_${index}.png`),fullPage:true}).catch(()=>{})));await browser?.close().catch(()=>{});console.error('Interactive browser setup failed; inspect browser_failure.json in the demo directory.');process.exit(1)}
process.on('uncaughtException',fail)
process.on('unhandledRejection',fail)
const headless=process.env.SHIELDVI_DEMO_BROWSER_HEADLESS==='1',password=process.env.LIVE_TEST_PASSWORD
browser=await chromium.launch({channel:'chrome',headless})
for(const [name,url,button] of [
 ['live_alice',process.env.LIVE_TEST_WEB+'/live.html?thread='+process.env.LIVE_TEST_THREAD,'Đăng nhập'],
 ['live_bob',process.env.LIVE_TEST_WEB+'/live.html?thread='+process.env.LIVE_TEST_THREAD,'Đăng nhập'],
 ['live_carol',process.env.LIVE_TEST_WEB+'/live.html','Đăng nhập'],
 ['live_dave',process.env.LIVE_TEST_WEB+'/live.html','Đăng nhập'],
 ['live_emma',process.env.LIVE_TEST_WEB+'/live.html','Đăng nhập'],
 ['live_admin',process.env.LIVE_TEST_ADMIN+'/live.html','Đăng nhập kiểm duyệt'],
 ['live_admin',process.env.LIVE_TEST_ADMIN+'/studio.html','Đăng nhập Studio']]){
 if(process.env.SHIELDVI_DEMO_VISUAL_MODE&&['live_carol','live_dave','live_emma'].includes(name))continue
 // Headed demo windows must follow real Chrome resizing. A fixed Playwright
 // viewport leaves the rendered surface at 1250px when the OS window changes.
 const context=await browser.newContext({viewport:headless?{width:1250,height:950}:null}),page=await context.newPage();pages.push(page)
 if(!headless)await configureDemoDownloads(context,page,process.env.SHIELDVI_DEMO_ROOT)
 const note=value=>fs.appendFileSync(path.join(process.env.SHIELDVI_DEMO_ROOT,'browser_network.jsonl'),JSON.stringify({at:Date.now(),account:name,...value})+'\n')
 page.on('response',response=>{const u=new URL(response.url());if(u.pathname.startsWith('/api/'))note({route:u.pathname,status:response.status()})})
 page.on('requestfailed',request=>{const u=new URL(request.url());if(u.pathname.startsWith('/api/'))note({route:u.pathname,error:request.failure()?.errorText})})
 await page.goto(url,{waitUntil:'domcontentloaded'});await page.getByLabel('Tên tài khoản').fill(name);await page.getByLabel('Mật khẩu',{exact:true}).fill(password);await page.getByRole('button',{name:button,exact:true}).click();await expect(page.getByRole('button',{name:'Đăng xuất',exact:true})).toBeVisible({timeout:20000})
}
if(process.env.SHIELDVI_DEMO_VISUAL_MODE){const {runVisualChecks}=await import('../reports/task_rollout_20261104/browser_visual_fix_20261105.mjs');await runVisualChecks(pages,browser,process.env.SHIELDVI_DEMO_ROOT,{audit:process.env.SHIELDVI_DEMO_VISUAL_MODE==='before'})}
if(headless){const studio=pages[6];for(const [button,heading] of [['Labeling','Labeling · Blind mode'],['Training','Training · CPU head-only'],['Models & Evaluation','Models & Evaluation']]){await studio.getByRole('button',{name:button,exact:true}).click();await expect(studio.getByRole('heading',{name:heading,exact:true})).toBeVisible();await expect(studio.getByRole('alert')).toHaveCount(0)}
 if(process.env.SHIELDVI_DEMO_V1_UNAVAILABLE==='1'){
  await expect(studio.getByTestId('baseline-unavailable')).toBeVisible()
  await expect(studio.getByRole('button',{name:'Đánh giá paired synthetic',exact:true})).toBeDisabled()
  await expect(studio.getByRole('row').filter({has:studio.getByRole('cell',{name:'v1',exact:true})})).toContainText('UNAVAILABLE')
  await studio.screenshot({path:path.join(process.env.SHIELDVI_DEMO_ROOT,'studio_missing_v1.png'),fullPage:true})
 }
 let feed=null
 if(process.env.SHIELDVI_DEMO_FEED_CHECK==='1'){const {runFeedChecks}=await import('../reports/social_feed_v2_20261104/browser_feed.mjs');feed=await runFeedChecks(pages,process.env.SHIELDVI_DEMO_ROOT)}
 if(process.env.SHIELDVI_DEMO_STUDIO_CHECK==='1'){
  for(const task of ['T039','T040']){
   const script=new URL(`../reports/task_rollout_20261104/browser_${task.toLowerCase()}.mjs`,import.meta.url)
   const result=await promisify(execFile)(process.execPath,[script.pathname.replace(/^\/([A-Za-z]:)/,'$1')],{env:process.env,windowsHide:true,timeout:120000})
   fs.writeFileSync(path.join(process.env.SHIELDVI_DEMO_ROOT,task+'_browser.log'),result.stdout+result.stderr)
  }
 }
 fs.writeFileSync(path.join(process.env.SHIELDVI_DEMO_ROOT,'browser_smoke.json'),JSON.stringify({status:'PASS',contexts:pages.length,social_accounts:5,login_automated_without_credentials_in_url:true,studio_tabs:3,no_training_started:true,headless:true,missing_v1_safely_blocked:process.env.SHIELDVI_DEMO_V1_UNAVAILABLE==='1',feed},null,2))}
await new Promise(resolve=>browser.on('disconnected',resolve))
