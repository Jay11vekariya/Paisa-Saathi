import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { money } from '../../utils/format';
export default function CategoryBreakdown({categories,total}) {
 const top=categories.slice(0,5);
 const rest=categories.slice(5).reduce((sum,c)=>sum+c.amount,0);
 const chart=rest ? [...top,{name:'Other categories',amount:rest,percentage:total ? rest/total*100:0}] : top;
 return <section className="glass category-card"><div className="section-heading"><div><span className="eyebrow">THE EVERYDAY DETAILS</span><h2>Where it goes</h2></div><span className="subtle-tag">THIS PERIOD</span></div><div className="category-chart"><ResponsiveContainer width="100%" height={210}><PieChart><Pie data={chart} dataKey="amount" nameKey="name" innerRadius={72} outerRadius={92} paddingAngle={3} stroke="none" isAnimationActive={false}>{chart.map((c,i)=><Cell key={c.name} fill={`var(--chart-${i})`}/>)}</Pie><Tooltip formatter={money} contentStyle={{background:'var(--tooltip-bg)',border:'1px solid var(--glass-border)',borderRadius:16}}/></PieChart></ResponsiveContainer><div className="category-total"><small>Total outgoings</small><strong>{money(total)}</strong></div></div><div className="category-legend">{chart.map((c,i)=><div key={c.name}><i style={{background:`var(--chart-${i})`}}/><span>{c.name}</span><strong>{c.percentage.toFixed(1)}%</strong></div>)}</div><details className="chart-data"><summary>All categories & amounts</summary><div className="chart-data-list">{categories.map(c=><div key={c.name}><span>{c.name}</span><span>{money(c.amount)}</span></div>)}</div></details></section>;
}
