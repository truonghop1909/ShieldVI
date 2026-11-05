import {chromium} from '../../../apps/moderation-web/node_modules/playwright/index.mjs';
import fs from 'node:fs';
const [url,out]=process.argv.slice(2);const browser=await chromium.launch({headless:true,channel:'chrome'});
try {
  const page=await browser.newPage();const writes=[],external=[],errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  page.on('request',r=>{if(r.method()!=='GET')writes.push(r.url());if(new URL(r.url()).origin!==new URL(url).origin)external.push(r.url())});
  await page.goto(url);await page.locator('#manual-intake-tools').waitFor({state:'visible'});
  await page.locator('#reviewer').fill('readiness_test_only');await page.locator('#apply-reviewer').click();
  await page.locator('#round').selectOption('2');
  if(await page.locator('#round').inputValue()!=='2')throw Error('Round2 unavailable');
  if(!await page.locator('#manual-intake').isEnabled())throw Error('Manual intake disabled');
  const response=await page.request.get(url+'/api/readiness');const ready=await response.json();
  if(ready.candidate_threads!==0||ready.model_predictions_enabled!==false)throw Error('Unexpected test corpus/predictions');
  await page.screenshot({path:out+'/review_empty.png',fullPage:true});
  if(writes.length||external.length||errors.length)throw Error(JSON.stringify({writes,external,errors}));
  fs.writeFileSync(out+'/review_browser.json',JSON.stringify({status:'PASS',mode:'isolated_empty_real_review_UI',
    round2_selectable:true,intake_enabled:true,model_predictions_enabled:false,review_submissions:0,
    writes:0,external_requests:0,page_errors:errors,real_data_added:0,human_gold_created:false},null,2));
} finally {await browser.close()}
