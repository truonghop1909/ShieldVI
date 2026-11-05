import fs from 'node:fs/promises'
import http from 'node:http'
import path from 'node:path'
import {createRequire} from 'node:module'
const root=process.cwd(),out=path.join(root,'reports/ai_update/context_recovery_20261103')
const require=createRequire(path.join(root,'apps/moderation-web/package.json'))
const {chromium,expect}=require('@playwright/test')
const data=JSON.parse(await fs.readFile(path.join(out,'game_after_api.json'),'utf8'))
const reference=JSON.parse(await fs.readFile(path.join(root,'datasets/fixtures/context_recovery_v1/game_rank_30_reference.json'),'utf8'))
const build=path.join(out,'dashboard_build')
const server=http.createServer(async(req,res)=>{
 try{
  let relative=new URL(req.url,'http://127.0.0.1').pathname.replace(/^\/dashboard\/?/,'')||'index.html'
  const file=path.resolve(build,relative)
  if(!file.startsWith(build+path.sep)&&file!==path.join(build,'index.html')){res.writeHead(403);return res.end()}
  const content=await fs.readFile(file)
  res.setHeader('Content-Type',file.endsWith('.js')?'application/javascript':file.endsWith('.css')?'text/css':'text/html; charset=utf-8');res.end(content)
 }catch{res.writeHead(404);res.end()}
})
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve))
const base=`http://127.0.0.1:${server.address().port}`
let browser
try{
 browser=await chromium.launch({channel:'chrome',headless:true})
 const page=await browser.newPage({viewport:{width:1500,height:1000}})
 await page.route('**/*',async route=>{
  const url=new URL(route.request().url())
  if(url.origin!==base)return route.abort()
  if(url.pathname==='/health')return route.fulfill({json:{status:'ready',model_loaded:true,details:'Replay transport; scores originally real V1',model_path:null}})
  if(url.pathname==='/api/v2/analyze'){
   const request=route.request().postDataJSON()
   expect(request.thread_id).toBe(reference.thread_id)
   expect(request.comments).toHaveLength(30)
   expect(request.comments.every(c=>!('annotation' in c))).toBeTruthy()
   return route.fulfill({json:data})
  }
  return route.continue()
 })
 await page.goto(base+'/dashboard/')
 await page.locator('input[type=file]').setInputFiles(path.join(root,reference.input_file))
 await page.locator('#thread-editor').getByRole('button',{name:'Phân tích hội thoại',exact:true}).click()
 await expect(page.locator('[data-testid="assessment-c12"]')).toContainText('Kết quả hỗ trợ: CLEAN')
 for(const cid of ['c12','c16','c21','c23','c24']){
  const row=page.locator('tbody tr').filter({has:page.locator('.table-comment-id').filter({hasText:new RegExp('^'+cid+'\\s')})})
  await expect(row).toContainText('ViSoBERT nghi toxic')
  await expect(row).toContainText('Kết quả hỗ trợ: CLEAN')
  await expect(row).toContainText('Policy risk: REVIEW')
  await expect(row).toContainText('Công kích: Chưa xác định')
  await expect(row.locator('select')).toHaveValue('')
 }
 const c12=page.locator('tbody tr').filter({has:page.locator('.table-comment-id').filter({hasText:/^c12\s/})})
 await expect(c12).toContainText('Trả lời: U02')
 await expect(page.getByTestId('assessment-c21').locator('..')).toContainText('Nhận lỗi')
 await expect(page.getByText('Hỗ trợ ngữ cảnh: 4 TOXIC; cần kiểm duyệt',{exact:true})).toBeVisible()
 const downloadPromise=page.waitForEvent('download')
 await page.getByRole('button',{name:'CSV AI',exact:true}).click()
 const download=await downloadPromise,stream=await download.createReadStream();let csv=''
 for await(const chunk of stream)csv+=chunk.toString('utf8')
 for(const field of ['toxicity_score','toxic_for_moderation','context_assessment_label','policy_risk_band','reply_to_user_id','directed_at_user_id'])expect(csv.split(/\r?\n/)[0]).toContain(field)
 await fs.writeFile(path.join(out,'dashboard_browser_smoke.json'),JSON.stringify({status:'PASS',transport:'Recorded API response replay; raw scores originally real V1',focus_rows:5,raw_and_assessment_separate:true,reply_target_separate:true,csv_fields_separate:true,human_labels_saved:0,external_requests_allowed:false},null,2)+'\n')
 console.log('Dashboard browser PASS: five raw-positive/context-CLEAN rows, reply/target and CSV separate, no human labels saved')
}catch(error){
 await fs.writeFile(path.join(out,'dashboard_browser_smoke.json'),JSON.stringify({status:'FAIL',error:String(error)},null,2)+'\n');throw error
}finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve))}

