import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight, ArrowDownLeft, Wallet, CreditCard, Sparkles, HeartPulse, ShieldCheck, MessageCircle, Calculator, MoveUpRight } from 'lucide-react';
import { useDashboard } from '../hooks/useDashboard';
import DataState from '../components/common/DataState';
import CustomerSwitcher from '../components/dashboard/CustomerSwitcher';
import FinancialHealthCard from '../components/dashboard/FinancialHealthCard';
import FinancialStateCard from '../components/dashboard/FinancialStateCard';
import FinancialInsights from '../components/dashboard/FinancialInsights';
import MetricCard from '../components/dashboard/MetricCard';
import Transactions from '../components/dashboard/Transactions';
import Spending from '../components/dashboard/Spending';
import CategoryBreakdown from '../components/dashboard/CategoryBreakdown';

const actions = [['/chat',MessageCircle,'Ask Saathi'],['/financial-health',HeartPulse,'Financial health'],['/recommendations',Sparkles,'Recommendations'],['/security',ShieldCheck,'Security'],['/loan-simulator',Calculator,'Loan simulator']];

export default function Dashboard() {
  const {dashboard:d,status,retry,customer}=useDashboard();
  const period=d ? new Date(d.period.month+'-01T12:00:00').toLocaleDateString('en-IN',{month:'long',year:'numeric'}) : 'Completed-month overview';
  return <>
    <div className="page-heading dashboard-heading"><div><span className="eyebrow">YOUR MONEY. YOUR MOMENTUM.</span><h1>Good morning{customer ? ', '+customer.name.split(' ')[0]:''}.</h1><p>Your financial picture, simplified.</p></div><CustomerSwitcher/></div>
    <div className="overview-context"><span className={`sync-status ${status==='connected'?'synced':''}`}><i/>{status==='connected'?(d.source==='test-fixture'?'UI test fixture · Not Atlas':'Financial system synced'):status==='loading'?'Connecting your financial picture':'Connection unavailable'}</span><span>{period} <b>·</b> Synthetic banking data</span></div>
    {status!=='connected'?<DataState status={status} retry={retry}/>:<>
      <div className="hero-grid"><FinancialHealthCard health={d.financial_health}/><FinancialStateCard state={d.financial_state} metrics={d.metrics} period={d.period}/></div>
      <FinancialInsights stress={d.financial_stress} segmentation={d.segmentation}/>
      <div className="metrics-grid"><MetricCard label="Monthly income" value={d.metrics.monthly_income} Icon={ArrowDownLeft} change={d.metrics.income_change_pct} context="Recorded income this period"/><MetricCard label="Monthly outgoings" value={d.metrics.monthly_expenses} Icon={ArrowUpRight} change={d.metrics.expense_change_pct} context="Includes EMI and investments" reverse neutral={d.metrics.emi_payment_gap}/><MetricCard label="Net savings" value={d.metrics.monthly_savings} Icon={Wallet} change={d.metrics.savings_change_pct} context={`${d.metrics.savings_rate}% of income retained`}/><MetricCard label="Scheduled EMI" value={d.metrics.monthly_emi} Icon={CreditCard} change={d.metrics.emi_change_pct} context={`${d.metrics.emi_burden}% of income · Trend: payments recorded`} neutral/></div>
      <div className="analysis-grid"><Spending spending={d.spending} period={d.period}/><CategoryBreakdown categories={d.spending.categories} total={d.metrics.monthly_expenses}/></div>
      <div className="activity-grid"><Transactions transactions={d.recent_transactions}/><section className="glass calculated-insight"><div className="section-heading"><span className="round-icon"><Sparkles size={23}/></span><span className="subtle-tag">FROM YOUR NUMBERS</span></div><span className="eyebrow">PAISA SAATHI INSIGHT</span><h2>A little clarity for <br/>your next step.</h2><p>{d.insight}</p><Link to="/financial-health">View analysis <MoveUpRight size={18}/></Link><small>Calculated using transparent rules. No generative AI.</small></section></div>
      <section className="quick-section"><div className="section-heading"><h2>Your Saathi, a tap away.</h2><span className="muted">Understand first. Recommend second.</span></div><div className="quick-actions">{actions.map(([url,Icon,label])=><Link key={url} to={url}><span className="round-icon"><Icon size={21}/></span><span>{label}</span></Link>)}</div></section>
      <p className="demo-disclaimer">Fictional profiles. Real calculations. Prototype wellness insights, not credit scores or lending decisions.</p>
    </>}
  </>;
}
