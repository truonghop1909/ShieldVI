import React from 'react'

// Native checkboxes support touch and long identifiers without Ctrl/Command.
export default function ChoiceList({legend,options,selected,onChange,maximum}){
 return <fieldset className="studio-choices"><legend>{legend}</legend>{options.length?options.map(option=><label key={option.id}><input type="checkbox" checked={selected.includes(option.id)} disabled={!selected.includes(option.id)&&selected.length>=maximum} onChange={event=>onChange(event.target.checked?[...selected,option.id]:selected.filter(id=>id!==option.id))}/><span>{option.label}</span></label>):<p>Chưa có lựa chọn phù hợp.</p>}</fieldset>
}
