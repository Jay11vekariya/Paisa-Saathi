import React from 'react';
import { TrendingUp, ShieldCheck, Activity, HeartHandshake, ArrowUpRight, Check } from 'lucide-react';
import { Link } from 'react-router-dom';
const icons={GROWTH:TrendingUp,NORMAL:Activity,CAUTION:ShieldCheck,SUPPORT:HeartHandshake};
export default function FinancialStateCard({state,metrics}) {
 const Icon=icons[state.state];
 return <section className={`glass financial-state state-${state.state.toLowerCase()}`}><div className="state-top"><span className="eyebrow">YOUR FINANCIAL STATE</span><span className="subtle-tag">RULE-BASED ANALYSIS</span></div><div className="state-main"><div><span className="state-pill"><Icon size={15}/>{state.state}</span><h2>{state.title}</h2><p>{state.description}</p></div><div className="state-symbol" aria-hidden="true"><div><Icon size={43} strokeWidth={1.4}/></div></div></div><div className="state-signals"><div><span>Savings</span><strong>{metrics.monthly_savings<0?'In deficit':metrics.savings_change_amount>0?'↗ Improving':metrics.savings_change_amount<0?'↘ Decreasing':'→ Steady'}</strong></div><div><span>Income</span><strong>{metrics.income_disruption?'↘ Disrupted':'→ Consistent'}</strong></div><div><span>EMI</span><strong>{metrics.emi_payment_gap?'Review payments':metrics.emi_burden>35?'High burden':'→ Manageable'}</strong></div></div><div className="state-focus"><Check size={16}/><span>{state.recommended_focus}</span></div><Link className="text-link" to="/financial-health">Understand your financial state <ArrowUpRight size={16}/></Link></section>;
}


