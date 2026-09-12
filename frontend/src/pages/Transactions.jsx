import React, {useEffect,useState} from 'react';
import { AlertTriangle, ChevronDown, ShieldAlert, TrendingUp } from 'lucide-react';
import { useDashboard } from '../hooks/useDashboard';
import { getTransactions, getMyTransactions, getAnomalies } from '../services/api';
import { TransactionList } from '../components/dashboard/Transactions';
import CustomerSwitcher from '../components/dashboard/CustomerSwitcher';
import DataState from '../components/common/DataState';
export default function TransactionsPage() {
 const {customerId,customer,signedIn}=useDashboard();
 const [page,setPage]=useState(1),[result,setResult]=useState(null),[status,setStatus]=useState('loading'),[attempt,setAttempt]=useState(0);
 const [alerts,setAlerts]=useState(null);
 useEffect(()=>{setPage(1);setResult(null);},[customerId]);
 useEffect(()=>{let active=true;setStatus('loading');(signedIn?getMyTransactions(page):getTransactions(customerId,page)).then(data=>{if(active){setResult(data);setStatus('connected');}}).catch(()=>{if(active)setStatus('error');});return()=>{active=false;};},[customerId,page,attempt,signedIn]);
 useEffect(()=>{let active=true;getAnomalies().then(data=>{if(active)setAlerts(data)}).catch(()=>{if(active)setAlerts(null)});return()=>{active=false};},[customerId,attempt]);
 return <><div className="page-heading"><div><span className="eyebrow">EVERYDAY MONEY, IN FOCUS</span><h1>Transaction history</h1><p>{customer?.name || 'Synthetic profile'} · {result?.source === 'test-fixture' ? 'UI test fixture · Not Atlas' : 'Credits and debits from MongoDB'}</p></div><CustomerSwitcher/></div>
 {alerts && <section className="activity-alerts"><div className="section-heading"><div><span className="eyebrow">UNUSUAL ACTIVITY</span><h2>Activity alerts</h2><p>{alerts.explanation}</p></div><ShieldAlert size={22}/></div>
  <div className="alert-summary"><div className="glass"><AlertTriangle/><span>Total alerts</span><strong>{alerts.summary.total_alerts}</strong></div><div className="glass"><ShieldAlert/><span>High risk alerts</span><strong>{alerts.summary.high_risk_alerts}</strong></div><div className="glass"><TrendingUp/><span>Spending behaviour</span><strong>{alerts.summary.spending_behaviour}</strong></div></div>
  {alerts.status==='insufficient_data'?<div className="glass alert-empty"><strong>More history needed</strong><p>{alerts.missing_information.join(' · ')}</p></div>:alerts.recent_anomalies.length?<div className="alert-list">{alerts.recent_anomalies.map(item=><details className={`glass anomaly anomaly-${item.severity.toLowerCase()}`} key={item.anomaly_id}><summary><span className="severity-badge">{item.severity}</span><div><strong>{item.title}</strong><small>{item.merchant || 'Scheduled payment'} · {item.date || 'Current period'}</small></div>{item.amount!=null&&<b>₹{item.amount.toLocaleString('en-IN')}</b>}<ChevronDown/></summary><div className="anomaly-detail"><span>WHY WAS THIS FLAGGED?</span><p>{item.explanation}</p><ul>{item.detected_signals.map(signal=><li key={signal}>{signal}</li>)}</ul><strong>Recommended action</strong><p>{item.recommended_action}</p><small>Confidence {Math.round(item.confidence*100)}% · Anomaly indicator, not proof of fraud.</small></div></details>)}</div>:<div className="glass alert-empty"><strong>No unusual activity detected</strong><p>Recent activity remains within this profile’s typical pattern.</p></div>}
 </section>}
 {status!=='connected'||result?.customer_id!==customerId||result?.page!==page?<DataState status={status==='error'?'error':'loading'} retry={()=>setAttempt(n=>n+1)}/>:<section className="glass history-panel"><div className="section-heading"><h2>{result.total} transactions</h2><span className="subtle-tag">SYNTHETIC DATA</span></div><TransactionList transactions={result.transactions}/><div className="pagination"><button className="glass-button" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {page} of {Math.max(1,result.pages)}</span><button className="glass-button" disabled={page>=result.pages} onClick={()=>setPage(p=>p+1)}>Next</button></div></section>}</>;
}


