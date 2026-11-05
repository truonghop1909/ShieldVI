const fs=require('fs');
const path=require('path');
const ROOT=path.resolve(__dirname,'../../..');
const {chromium}=require(path.join(ROOT,'apps/moderation-web/node_modules/@playwright/test'));
(async()=>{
  const browser=await chromium.launch({headless:true,channel:'chrome'});
  const page=await browser.newPage();const errors=[],outside=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:8010/'))outside.push(r.url());});
  try{
    await page.goto('http://127.0.0.1:8010/',{waitUntil:'networkidle'});
    await page.locator('#manual-intake-tools').waitFor({state:'visible'});
    await page.waitForFunction(()=>document.querySelector('#readiness').textContent.includes('0/200'));
    if(!(await page.locator('#manual-intake').isEnabled()))throw Error('Manual intake disabled');
    if(!(await page.locator('#reviewer').isEnabled()))throw Error('Reviewer ID entry disabled');
    const session=await page.evaluate(async()=>{const r=await fetch('/session');const j=await r.json();return {mode:j.mode,blind_review:j.blind_review,model_predictions_enabled:j.model_predictions_enabled};});
    if(!session.blind_review||session.model_predictions_enabled||errors.length||outside.length)throw Error('Blind local review invariant failed');
    await page.screenshot({path:path.join(__dirname,'review_ui.png'),fullPage:true});
    fs.writeFileSync(path.join(__dirname,'review_browser.json'),JSON.stringify({status:'PASS',session,manual_intake_enabled:true,reviewer_entry_enabled:true,real_candidate_threads:0,no_labels_submitted:true,page_errors:errors,external_requests:outside},null,2));
    process.stdout.write('BLIND_REVIEW_UI_PASS; no data or labels submitted\n');
  }finally{await browser.close();}
})().catch(e=>{process.stderr.write(e.message+'\n');process.exitCode=1;});
