const configured=(import.meta.env.VITE_SOCIAL_API_BASE || '').trim()
if(configured){const url=new URL(configured);if(!['http:','https:'].includes(url.protocol)||url.username||url.password||url.pathname!=='/'||url.search||url.hash)throw new Error('API base must be an exact HTTP(S) origin')}
const base=configured.replace(/\/$/,'')
export function apiClient(token,onExpired=()=>{},scope){
  return async function request(path,{method='GET',body,signal}={}){
    const deadline=AbortSignal.timeout(15000),combined=AbortSignal.any([deadline,signal,scope].filter(Boolean))
    try{
      const response=await fetch(`${base}/api/v1${path}`,{method,signal:combined,cache:'no-store',credentials:'omit',
        headers:{Accept:'application/json',...(token?{Authorization:`Bearer ${token}`} : {}),...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined})
      if(combined.aborted)throw combined.reason
      if(response.status===401&&token)onExpired()
      if(!response.ok){const messages={401:'Phiên đăng nhập không hợp lệ.',403:'Tài khoản không có quyền kiểm duyệt.',404:'Không tìm thấy nội dung.',409:'Phiên bản hoặc người duyệt đã thay đổi. Hãy tải lại chi tiết.',422:'Kiểm tra lý do và dữ liệu nhập.',429:'Thao tác quá nhanh. Vui lòng thử lại sau.'};throw new Error(messages[response.status] || 'Máy chủ chưa xử lý được yêu cầu.')}
      const result=response.status===204?null:await response.json();if(combined.aborted)throw combined.reason;return result
    }catch(error){if(signal?.aborted||scope?.aborted)throw new DOMException('Canceled','AbortError');if(deadline.aborted)throw new Error('Máy chủ phản hồi quá lâu. Tải lại để kiểm tra kết quả trước khi thử tiếp.');if(error instanceof TypeError)throw new Error('Không kết nối được máy chủ. Vui lòng thử lại.');throw error}
  }
}
export const versions=row=>({expected_revision:row.content_revision,expected_decision_version:row.decision_version})
