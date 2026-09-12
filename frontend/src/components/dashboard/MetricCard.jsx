import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import { money } from '../../utils/format';
export function Trend({value,reverse=false,neutral=false}) {
 const Icon = value===null || Math.abs(value)<.05 ? Minus : value>0 ? ArrowUpRight : ArrowDownRight;
 const favorable = !neutral && value!==null && (reverse ? value<0 : value>0);
 return <span className={`trend ${favorable?'favorable':''}`}><Icon size={14}/>{value===null?'No comparable baseline':Math.abs(value)<.05?'Stable':`${value>0?'+':''}${value.toFixed(1)}%`}<small>vs previous month</small></span>;
}
export default function MetricCard({label,value,Icon,change,context,reverse,neutral}) {
 return <section className="glass metric-card"><div className="metric-top"><span>{label}</span><span className="round-icon"><Icon size={19}/></span></div><strong className="metric-number">{money(value)}</strong><Trend value={change} reverse={reverse} neutral={neutral}/><p>{context}</p></section>;
}

