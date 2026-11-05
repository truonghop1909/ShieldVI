// Unique, readable names keep repeated operator exports from replacing a file.
export function saveBlob(blob,name){
 const safe=String(name||'export.json').replace(/[<>:"/\\|?*\u0000-\u001f]/g,'_').replace(/^[. ]+|[. ]+$/g,'')
 const extension=safe.match(/\.[A-Za-z0-9]{1,8}$/)?.[0]||''
 const base=(extension?safe.slice(0,-extension.length):safe).slice(0,80)||'export'
 const stamp=new Date().toISOString().replace(/[-:]/g,'').replace('T','_').replace('.','_').replace('Z','')
 const nonce=[...crypto.getRandomValues(new Uint32Array(2))].map(n=>n.toString(16).padStart(8,'0')).join('')
 const filename=`${base}_${stamp}_${nonce}${extension}`
 const url=URL.createObjectURL(blob),link=document.createElement('a')
 link.href=url;link.download=filename;link.hidden=true;document.body.append(link)
 try{link.click()}finally{link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000)}
 return filename
}
