import React,{useEffect,useState} from 'react';
import {Calculator,CheckCircle2,Lightbulb,TriangleAlert} from 'lucide-react';
import {simulateLoan} from '../services/api';

const money=value=>value==null?'—':`₹${Number(value).toLocaleString('en-IN',{maximumFractionDigits:0})}`;
const pct=value=>value==null?'—':`${Number(value).toFixed(1)}%`;

export default function LoanSimulator(){
 const [form,setForm]=useState({loan_amount:500000,annual_interest_rate:10.5,tenure_months:60,purpose:'Personal requirement'});
 const [result,setResult]=useState(null),[status,setStatus]=useState('loading'),[error,setError]=useState('');
 useEffect(()=>{const controller=new AbortController();const timer=setTimeout(()=>{setStatus('loading');setError('');simulateLoan({...form,loan_amount:Number(form.loan_amount),annual_interest_rate:Number(form.annual_interest_rate),tenure_months:Number(form.tenure_months)},{signal:controller.signal}).then(data=>{setResult(data);setStatus('ready')}).catch(err=>{if(err.name!=='AbortError'){setError(err.message);setStatus('error')}})},350);return()=>{clearTimeout(timer);controller.abort()}},[form]);
 const update=e=>setForm(current=>({...current,[e.target.name]:e.target.value}));
 const current=result?.current_financial_snapshot,projected=result?.projected_financial_snapshot;
 return <><div className="page-heading"><div><span className="eyebrow">BORROW WITH CONTEXT</span><h1>Loan impact simulator</h1><p>See how a possible loan could change your real recorded financial position.</p></div><Calculator/></div>
 <section className="loan-workspace">
  <form className="glass loan-form" onSubmit={e=>e.preventDefault()}><span className="eyebrow">LOAN INPUTS</span><h2>Explore a scenario</h2>
   <label>Loan amount<input name="loan_amount" type="number" min="1" value={form.loan_amount} onChange={update}/></label>
   <label>Annual interest rate (%)<input name="annual_interest_rate" type="number" min="0" max="100" step="0.1" value={form.annual_interest_rate} onChange={update}/></label>
   <label>Tenure<select name="tenure_months" value={form.tenure_months} onChange={update}><option value="12">1 year</option><option value="24">2 years</option><option value="36">3 years</option><option value="60">5 years</option><option value="84">7 years</option><option value="120">10 years</option><option value="180">15 years</option><option value="240">20 years</option></select></label>
   <label>Loan purpose<input name="purpose" maxLength="120" value={form.purpose} onChange={update}/></label><small>Results update automatically and use your authenticated financial snapshot.</small>
  </form>
  <div className={`glass loan-result impact-${(result?.impact_level||'loading').toLowerCase().replace(' ','-')}`}><span className="eyebrow">LIVE RESULT</span>{status==='loading'?<p>Calculating financial impact…</p>:status==='error'?<p className="form-message">{error}</p>:result?.status==='insufficient_data'?<><h2>More information needed</h2><p>{result.missing_information.join(', ')}</p></>:<><div className="impact-heading"><div><small>IMPACT LEVEL</small><strong>{result.impact_level}</strong></div><b>{result.impact_score}<span>/100</span></b></div><div className="loan-totals"><div><span>Monthly EMI</span><strong>{money(result.emi)}</strong></div><div><span>Total interest</span><strong>{money(result.total_interest)}</strong></div><div><span>Total repayment</span><strong>{money(result.total_repayment)}</strong></div></div><p>{result.recommendation}</p><small>{result.disclaimer}</small></>}</div>
 </section>
 {current&&projected&&<><section className="comparison-section"><div className="section-heading"><div><span className="eyebrow">CURRENT VS PROJECTED</span><h2>Your financial position</h2></div></div><div className="comparison-grid"><div className="glass comparison-card"><strong>CURRENT FINANCIAL POSITION</strong><Comparison data={current}/></div><div className="comparison-arrow">→</div><div className="glass comparison-card projected"><strong>AFTER THIS LOAN</strong><Comparison data={projected}/></div></div></section>
 <section className="loan-explanations"><div className="glass"><TriangleAlert/><span className="eyebrow">WHY THIS RESULT?</span>{result.key_impacts.map(item=><p key={item}>{item}</p>)}{result.risk_factors.map(item=><div className="impact-item risk" key={item}><TriangleAlert size={15}/>{item}</div>)}{result.positive_factors.map(item=><div className="impact-item positive" key={item}><CheckCircle2 size={15}/>{item}</div>)}</div><div className="glass"><Lightbulb/><span className="eyebrow">SAFER ALTERNATIVE</span><ul>{result.safer_alternative.map(item=><li key={item}>{item}</li>)}</ul></div></section></>}
 </>;
}

function Comparison({data}){return <dl><div><dt>Monthly surplus</dt><dd>{money(data.monthly_surplus)}</dd></div><div><dt>EMI burden</dt><dd>{pct(data.emi_burden_pct)}</dd></div><div><dt>Savings capacity</dt><dd>{pct(data.savings_capacity_pct)}</dd></div><div><dt>Emergency buffer</dt><dd>{data.emergency_buffer_months.toFixed(1)} months</dd></div><div><dt>Financial stress</dt><dd>{data.financial_stress_score??'—'}/100</dd></div></dl>}
