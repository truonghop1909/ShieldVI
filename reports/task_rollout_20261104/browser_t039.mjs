import {createRequire} from 'node:module'
import fs from 'node:fs'
import path from 'node:path'
import assert from 'node:assert/strict'
const require=createRequire(new URL('../../apps/social-web/package.json',import.meta.url)),{chromium,expect}=require('@playwright/test')
const out=process.env.LIVE_TEST_ARTIFACTS,web=process.env.LIVE_TEST_ADMIN,password=process.env.LIVE_TEST_PASSWORD,browser=await chromium.launch({channel:'chrome',headless:true}),context=await browser.newContext(),page=await context.newPage(),checks=[]
try{
 await page.goto(web+'/studio.html');await page.getByLabel('Tên tài khoản').fill('live_admin');await page.getByLabel('Mật khẩu',{exact:true}).fill(password);await page.getByRole('button',{name:'Đăng nhập Studio',exact:true}).click();await expect(page.getByRole('heading',{name:'Datasets',exact:true})).toBeVisible();checks.push('admin_authenticated_studio')
 const source='body,y,thread_id,comment_id,user_id,timestamp\nChiều thứ bảy nhóm mình sắp xếp khu đọc sách ở tầng một nhé.,0,STUDIO_BROWSER_1,c1,A,2026-11-04T00:00:00Z\nMình đem thêm đèn bàn và giấy ghi chú để mọi người chọn sách dễ hơn.,0,STUDIO_BROWSER_1,c2,B,2026-11-04T00:01:00Z\n'
 const inputFile=path.join(out,'T039_synthetic_browser.csv');fs.writeFileSync(inputFile,source)
 await page.getByLabel('File dataset (UTF-8, tối đa 1 MiB)').setInputFiles(inputFile)
 await page.getByLabel('Mapping cột (JSON: tên chuẩn → cột nguồn)').fill(JSON.stringify({text:'body',label:'y'}))
 await page.getByRole('button',{name:'Kiểm tra và tạo phiên bản',exact:true}).click();await expect(page.getByTestId('dataset-result')).toContainText('ACCEPTED',{timeout:30000});await expect(page.getByTestId('dataset-result')).toContainText('synthetic_reference');checks.push('utf8_file_upload_column_mapping_accepted_immutable_version')
 await expect(page.getByTestId('dataset-result')).toContainText('Chiều thứ bảy nhóm mình');await expect(page.getByTestId('dataset-result')).toContainText('U_');checks.push('preview_labels_pseudonyms_and_group_split')
 const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Export csv',exact:true}).click();const download=await downloadPromise;await download.saveAs(path.join(out,'T039_export.csv'));assert(fs.readFileSync(path.join(out,'T039_export.csv'),'utf8').includes('CLEAN'));checks.push('authenticated_csv_export')
 await page.getByRole('button',{name:'Kiểm tra và tạo phiên bản',exact:true}).click();await expect(page.getByTestId('dataset-result')).toContainText('ACCEPTED');await expect(page.locator('ul li')).toHaveCount(1);checks.push('repeat_upload_no_duplicate_version')
 await page.getByRole('textbox',{name:'Nội dung nhập',exact:true}).fill('[{"thread_id":"BAD","comment_id":"c1","user_id":"A","text":"Không nhãn hợp lệ","label":"WRONG","timestamp":"2026-11-04T00:00:00Z"}]')
 await page.getByRole('combobox',{name:'Định dạng',exact:true}).selectOption('json');await page.getByRole('textbox',{name:'Mapping cột (JSON: tên chuẩn → cột nguồn)',exact:true}).fill('{}');await page.getByRole('button',{name:'Kiểm tra và tạo phiên bản',exact:true}).click();await expect(page.getByTestId('dataset-result')).toContainText('REJECTED');await expect(page.getByTestId('dataset-result')).toContainText('INVALID_SCHEMA');checks.push('invalid_labels_reported_without_silent_drop')
 await page.screenshot({path:path.join(out,'T039_studio.png'),fullPage:true});fs.writeFileSync(path.join(out,'T039_browser_result.json'),JSON.stringify({status:'PASS',checks,source:'synthetic_browser_fixture_not_gold',neural_inference:false},null,2));console.log(JSON.stringify({status:'PASS',checks:checks.length}))
}catch(error){await page.screenshot({path:path.join(out,'T039_failure.png'),fullPage:true}).catch(()=>{});throw error}finally{await context.close();await browser.close()}
