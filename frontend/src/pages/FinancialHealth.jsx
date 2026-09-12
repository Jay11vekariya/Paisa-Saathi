import React from 'react';
import { useDashboard } from '../hooks/useDashboard';
import { money } from '../utils/format';
import FinancialHealthCard, {FactorList} from '../components/dashboard/FinancialHealthCard';
import FinancialStateCard from '../components/dashboard/FinancialStateCard';
import FinancialInsights from '../components/dashboard/FinancialInsights';
import CustomerSwitcher from '../components/dashboard/CustomerSwitcher';
import DataState from '../components/common/DataState';

export default function FinancialHealth() {
  const {dashboard:d,status,retry}=useDashboard();
  return <>
    <div className="page-heading"><div><span className="eyebrow">UNDERSTAND THE WHY</span><h1>Your financial wellbeing.</h1><p>Clear numbers. Transparent reasoning.</p></div><CustomerSwitcher/></div>
    {status!=='connected'?<DataState status={status} retry={retry}/>:<>
      <div className="overview-context"><span>Analysis for {d.customer.name}</span><span>{d.period.month} · Completed month</span></div>
      <div className="hero-grid"><FinancialHealthCard health={d.financial_health}/><FinancialStateCard state={d.financial_state} metrics={d.metrics}/></div>
      <FinancialInsights stress={d.financial_stress} segmentation={d.segmentation} detailed/>
      <div className="analysis-grid health-analysis"><section className="glass factor-panel"><span className="eyebrow">FIVE FACTORS. ONE CLEAR PICTURE.</span><h2>How your health score adds up</h2><FactorList health={d.financial_health}/></section><section className="glass reasons-panel"><span className="eyebrow">BEHIND YOUR FINANCIAL STATE</span><h2>{d.financial_state.title}</h2><ul>{d.financial_state.reasons.map(reason=><li key={reason}>{reason}</li>)}</ul><div className="buffer-stat"><small>Emergency buffer</small><strong>{d.metrics.emergency_buffer_months.toFixed(1)} <span>months</span></strong><p>{money(d.metrics.account_balance)} closing balance ÷ {money(d.metrics.average_monthly_expenses)} average monthly outgoings.</p></div><div className="buffer-stat"><small>Balance change this month</small><strong>{money(d.metrics.balance_change)}</strong><p>Opening balance plus recorded credits minus debits. Investments are counted as outgoings, not valued assets.</p></div></section></div>
      <p className="demo-disclaimer">{d.financial_health.methodology} {d.financial_stress.methodology} Analysis uses {d.period.start} through {d.period.month}; no partial-month comparison.</p>
    </>}
  </>;
}
