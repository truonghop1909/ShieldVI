import React from 'react'

export default function LabelDistribution({labels}){
 const counts=Object.entries(labels||{}).filter(([,count])=>Number.isFinite(count)&&count>=0),total=counts.reduce((sum,[,count])=>sum+count,0)
 if(!counts.length)return null
 return <div className="label-distribution" role="group" aria-label="Phân bố nhãn">{counts.map(([label,count])=><div key={label}><span>{label}</span><strong>{count}</strong><meter aria-label={label} min={0} max={Math.max(1,total)} value={count}>{count}/{total}</meter></div>)}</div>
}
