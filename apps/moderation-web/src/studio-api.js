const base=(import.meta.env.VITE_SOCIAL_API_BASE||'').trim().replace(/\/$/,'')
if(base){const u=new URL(base);if(!['http:','https:'].includes(u.protocol)||u.username||u.password||u.pathname!=='/'||u.search||u.hash)throw Error('API origin must be exact HTTP(S)')}
export function studioApi(token,onExpired){return async function request(path,{method='GET',body,signal,download=false,key}={}){
 const response=await fetch(`${base}/api/studio${path}`,{method,credentials:'omit',redirect:'error',cache:'no-store',signal:AbortSignal.any([signal,AbortSignal.timeout(30000)].filter(Boolean)),headers:{Authorization:`Bearer ${token}`,Accept:'application/json',...(body?{'Content-Type':'application/json'}:{}),...(key?{'Idempotency-Key':key}:{})},body:body?JSON.stringify(body):undefined})
 if(response.status===401)onExpired()
 if(!response.ok){const e=await response.json().catch(()=>({}));throw Error(typeof e.detail==='string'?e.detail:`Yêu cầu thất bại (${response.status}). Kiểm tra định dạng/quyền hoặc tải lại phiên bản.`)}
 return download?response.blob():response.json()
}}
export {saveBlob} from '../../shared/download-file.mjs'
