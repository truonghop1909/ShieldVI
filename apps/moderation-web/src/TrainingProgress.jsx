import React,{useId} from 'react'

function Metric({history,name,read}){
 const title=useId(),points=history.map((row,index)=>({epoch:row.epoch??index+1,value:read(row)})).filter(p=>Number.isFinite(p.value))
 if(!points.length)return null
 const maximum=Math.max(...points.map(p=>p.value),.000001),minimum=name==='Validation Macro-F1'?0:Math.min(0,...points.map(p=>p.value)),scale=name==='Validation Macro-F1'?1:maximum
 const coords=points.map((p,index)=>[24+index*272/Math.max(1,points.length-1),110-(p.value-minimum)*86/(scale-minimum)])
 return <figure><figcaption id={title}>{name}</figcaption><svg viewBox="0 0 320 140" role="img" aria-labelledby={title}><path d="M24 16V110H300" fill="none" stroke="#9db4a6"/><polyline points={coords.map(c=>c.join(',')).join(' ')} fill="none" stroke="#21664e" strokeWidth="2.5"/>{coords.map(([x,y],i)=><circle key={i} cx={x} cy={y} r="3.5" fill="#21664e"><title>Epoch {points[i].epoch}: {points[i].value.toFixed(4)}</title></circle>)}<text x="24" y="132" fontSize="11" fill="#526b60">Epoch {points[0].epoch}</text><text x="296" y="132" textAnchor="end" fontSize="11" fill="#526b60">{points.at(-1).value.toFixed(4)}</text></svg><small>{points.map(p=>`Epoch ${p.epoch}: ${p.value.toFixed(4)}`).join(' · ')}</small></figure>
}

// Do not fabricate a percentage: the existing API has no total-step contract.
export default function TrainingProgress({run}){
 const running=['QUEUED','RUNNING','CANCELLING'].includes(run.status),complete=run.status==='COMPLETED'
 const history=Array.isArray(run.metrics?.epochs)?run.metrics.epochs:[]
 return <div className="training-progress"><label htmlFor="training-progress">Tiến trình · {run.metrics?.stage||run.status}</label>
  {running?<progress id="training-progress" aria-label="Tiến trình training"/>:<progress id="training-progress" aria-label="Tiến trình training" max={1} value={complete?1:0}/>}
  <p>{running?'Chưa có phần trăm từ worker; trạng thái cập nhật tự động.':complete?'Worker đã hoàn tất. Xem metrics và manifest bên dưới.':'Job đã dừng; xem trạng thái và log bên dưới.'}</p>
  {history.length?<div className="training-charts"><Metric history={history} name="Mean batch loss" read={row=>row.mean_batch_loss}/><Metric history={history} name="Validation Macro-F1" read={row=>row.validation?.macro_f1}/></div>:<p>Chưa có metrics epoch từ worker.</p>}
 </div>
}
