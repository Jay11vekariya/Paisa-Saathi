import React, { useEffect, useState } from 'react';
import { AlertCircle, ArrowRight, CheckCircle2, ShieldAlert, Sparkles } from 'lucide-react';
import CustomerSwitcher from '../components/dashboard/CustomerSwitcher';
import DataState from '../components/common/DataState';
import { getRecommendations, getMyRecommendations } from '../services/api';
import { money } from '../utils/format';
import { useDashboard } from '../hooks/useDashboard';

const priorityCopy = { NOW: 'Start here', NEXT: 'A useful next step', CONSIDER: 'Consider when it fits your goals' };

function ProductName({ product }) {
  return <><span className="recommendation-category">{product.category}</span><h2>{product.product_name}</h2><p>{product.description}</p></>;
}

export default function Recommendations() {
  const { customerId, customer, status: dashboardStatus, signedIn } = useDashboard();
  const [data, setData] = useState(null);
  const [status, setStatus] = useState('loading');
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    setStatus('loading'); setData(null);
    (signedIn ? getMyRecommendations({ signal: controller.signal }) : getRecommendations(customerId, { signal: controller.signal }))
      .then(result => {
        if (!result.customer || !Array.isArray(result.recommendations) || !Array.isArray(result.not_recommended)) throw new Error('Unexpected recommendation response');
        if (active) { setData(result); setStatus('connected'); }
      })
      .catch(() => { if (active) setStatus('error'); });
    return () => { active = false; controller.abort(); };
  }, [customerId, retryCount, signedIn]);

  const loading = status === 'loading' || dashboardStatus === 'loading';
  return <><div className="page-heading dashboard-heading"><div><span className="eyebrow">EXPLAINABLE NEXT STEPS</span><h1>Recommendations for your situation.</h1><p>Guidance based on your calculated cash flow — never a sales target.</p></div><CustomerSwitcher/></div>
    {loading || status !== 'connected' ? <DataState status={loading ? 'loading' : 'error'} retry={() => setRetryCount(count => count + 1)}/> : <>
      <div className="overview-context"><span>Analysis for {data.customer.name}</span><span>{data.period.month} <b>·</b> Rule-based financial guidance</span></div>
      <section className="glass recommendation-hero"><div className="recommendation-hero-icon"><Sparkles size={28}/></div><div><span className="eyebrow">YOUR PRIORITY</span><h2>{data.recommended_focus}</h2><p>{data.financial_state} mode uses your income, outgoings, scheduled EMI, and emergency buffer to decide what is useful now.</p></div><div className="recommendation-stat"><small>Emergency buffer</small><strong>{data.metrics.emergency_buffer_months.toFixed(1)} <span>months</span></strong><small>{money(data.metrics.account_balance)} closing balance</small></div></section>
      <section className="recommendation-section"><div className="section-heading"><div><span className="eyebrow">PRIORITISED FOR YOU</span><h2>What may help now</h2></div><CheckCircle2 size={21}/></div><div className="recommendation-grid">{data.recommendations.map(item => <article className="glass recommendation-card" key={item.product.product_id}><div className="recommendation-card-top"><span className="priority-pill">{priorityCopy[item.priority]}</span><span className="risk-label">{item.suitability} · {item.confidence} confidence</span></div><ProductName product={item.product}/><div className="recommendation-action"><small>Suggested action</small><strong>{item.action}</strong><p>{item.reason}</p></div><div className="recommendation-reason"><strong>Why this?</strong><p>{item.why_this}</p></div><div className="recommendation-reason"><strong>Why it may help</strong><p>{item.why_it_may_help}</p></div><span className="recommendation-id">Fictional product · {item.product.product_id}</span></article>)}</div></section>
      {data.not_recommended.length > 0 && <section className="recommendation-section not-recommended-section"><div className="section-heading"><div><span className="eyebrow">PROTECT YOUR NEXT STEP</span><h2>Not a fit right now</h2><p>These are deliberately not recommended from the available financial data.</p></div><ShieldAlert size={21}/></div><div className="not-recommended-list">{data.not_recommended.map(item => <article className="glass not-recommendation" key={item.product.product_id}><div><ProductName product={item.product}/></div><div className="not-recommendation-reason"><strong><AlertCircle size={16}/> Why NOT this?</strong><p>{item.why_not_this}</p><small>What triggered this</small><ul>{item.rejection_conditions.map(condition => <li key={condition}>{condition}</li>)}</ul><div className="safer-alternative"><small>Safer alternative</small><strong>{item.safer_alternative.action}</strong><p>{item.safer_alternative.reason}</p></div></div><ArrowRight size={18} aria-hidden="true"/></article>)}</div></section>}
      <p className="demo-disclaimer">{data.methodology}</p>
    </>}
  </>;
}

