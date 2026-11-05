import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
import {configureDemoDownloads} from '../../scripts/demo_downloads.mjs'
const require=createRequire(new URL('../../apps/social-web/package.json',import.meta.url)),{chromium,expect}=require('@playwright/test')
const root=path.resolve('reports/download_fix_20261105_native_'+Date.now()),browser=await chromium.launch({channel:'chrome',headless:false}),checks=[]
fs.mkdirSync(root,{recursive:true})
const payload={text:'Xin chào, dữ liệu tiếng Việt giữ nguyên 🛡️',comments:[{id:'c01',label:'CLEAN'}]}
async function makePage(context,fixed=false){const p=await context.newPage();await p.setContent('<button>Tải JSON</button>');if(fixed){await p.addScriptTag({type:'module',content:fs.readFileSync('apps/shared/download-file.mjs','utf8')+'\nwindow.testSaveBlob=saveBlob'});await p.getByRole('button').evaluate((button,value)=>button.onclick=()=>window.testSaveBlob(new Blob([JSON.stringify(value)],{type:'application/json;charset=utf-8'}),'conversation_analysis.json'),payload)}else await p.getByRole('button').evaluate((button,value)=>button.onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(value)],{type:'application/json;charset=utf-8'}));a.download='conversation_analysis.json';a.click()},payload);return p}
async function click(p){const event=p.waitForEvent('download');await p.getByRole('button').click();return event}
try{
 const old=await browser.newContext({viewport:null}),oldPage=await makePage(old),bad=await click(oldPage),oldPath=await bad.path()
 assert.equal(bad.suggestedFilename(),'conversation_analysis.json');assert(!oldPath.endsWith('.json'));assert.deepEqual(JSON.parse(fs.readFileSync(oldPath,'utf8')),payload);checks.push('reproduced_correct_suggested_name_but_actual_uuid_without_extension_in_unfixed_context')
 const fixed=await browser.newContext({viewport:null}),p=await makePage(fixed,true),folder=await configureDemoDownloads(fixed,p,root)
 const good=await click(p),filename=good.suggestedFilename();assert.match(filename,/^conversation_analysis_\d{8}_\d{6}_\d{3}_[a-f0-9]{16}\.json$/)
 const file=path.join(folder,filename);await expect.poll(()=>fs.existsSync(file),{timeout:10000}).toBe(true);assert.deepEqual(JSON.parse(fs.readFileSync(file,'utf8')),payload);checks.push('actual_native_disk_filename_json_and_utf8_content_without_saveAs')
 const ui=await fixed.newPage();await ui.goto('chrome://downloads/');await expect(ui.getByRole('link',{name:filename,exact:true})).toBeVisible();await ui.screenshot({path:path.join(root,'chrome_download_name.png')});checks.push('chrome_downloads_ui_shows_json_filename')
 await click(p);await expect.poll(()=>fs.readdirSync(folder).filter(f=>f.endsWith('.json')).length).toBe(2);for(const name of fs.readdirSync(folder))assert.deepEqual(JSON.parse(fs.readFileSync(path.join(folder,name),'utf8')),payload);checks.push('repeat_export_keeps_both_files_without_overwriting')
 for(const [ext,type,text] of [['csv','text/csv','text,label\nXin chào,CLEAN\n'],['jsonl','application/x-ndjson',JSON.stringify(payload)+'\n']]){
  const next=p.waitForEvent('download');await p.evaluate(({ext,type,text})=>window.testSaveBlob(new Blob([text],{type}),'dataset.'+ext),{ext,type,text});const event=await next,name=event.suggestedFilename();assert(name.endsWith('.'+ext));await expect.poll(()=>fs.existsSync(path.join(folder,name))).toBe(true);assert.equal(fs.readFileSync(path.join(folder,name),'utf8'),text)
 }
 checks.push('shared_studio_csv_jsonl_extensions_and_utf8_content_preserved')
 const stillOld=await click(oldPage);assert(!(await stillOld.path()).endsWith('.json'));checks.push('configuration_scoped_to_fixed_context_only')
 await fixed.close();assert(fs.existsSync(file));checks.push('named_export_survives_browser_context_close')
 fs.writeFileSync(path.join(root,'result.json'),JSON.stringify({status:'PASS',checks,files:fs.readdirSync(folder),root},null,2));console.log(JSON.stringify({status:'PASS',checks:checks.length,root}))
}finally{await browser.close()}
