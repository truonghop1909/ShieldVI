import fs from 'node:fs'
import path from 'node:path'

// Playwright defaults to allowAndName (UUID files in a temporary directory).
// Operator windows need Chrome's normal filename handling and retained files.
export async function configureDemoDownloads(context,page,demoRoot){
 const folder=path.resolve(demoRoot,'downloads')
 fs.mkdirSync(folder,{recursive:true})
 const session=await context.newCDPSession(page)
 try{
  const {targetInfo}=await session.send('Target.getTargetInfo')
  if(!targetInfo.browserContextId)throw Error('Cannot scope demo downloads to this isolated browser context.')
  await session.send('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:folder,browserContextId:targetInfo.browserContextId,eventsEnabled:true})
 }catch(error){await session.detach();throw error}
 // Chromium resets this override when its owning CDP session detaches.
 // Keep it for the lifetime of the operator context, then release it.
 context.on('close',()=>session.detach().catch(()=>{}))
 return folder
}
