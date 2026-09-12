import React, {useEffect,useState} from 'react';
import { useDashboard } from '../hooks/useDashboard';
import { getTransactions } from '../services/api';
import { TransactionList } from '../components/dashboard/Transactions';
import CustomerSwitcher from '../components/dashboard/CustomerSwitcher';
import DataState from '../components/common/DataState';
export default function TransactionsPage() {
 const {customerId,customer}=useDashboard();
 const [page,setPage]=useState(1),[result,setResult]=useState(null),[status,setStatus]=useState('loading'),[attempt,setAttempt]=useState(0);
 useEffect(()=>{setPage(1);setResult(null);},[customerId]);
 useEffect(()=>{let active=true;setStatus('loading');getTransactions(customerId,page).then(data=>{if(active){setResult(data);setStatus('connected');}}).catch(()=>{if(active)setStatus('error');});return()=>{active=false;};},[customerId,page,attempt]);
 return <><div className="page-heading"><div><span className="eyebrow">EVERYDAY MONEY, IN FOCUS</span><h1>Transaction history</h1><p>{customer?.name || 'Synthetic profile'} · {result?.source === 'test-fixture' ? 'UI test fixture · Not Atlas' : 'Credits and debits from MongoDB'}</p></div><CustomerSwitcher/></div>{status!=='connected'||result?.customer_id!==customerId||result?.page!==page?<DataState status={status==='error'?'error':'loading'} retry={()=>setAttempt(n=>n+1)}/>:<section className="glass history-panel"><div className="section-heading"><h2>{result.total} transactions</h2><span className="subtle-tag">SYNTHETIC DATA</span></div><TransactionList transactions={result.transactions}/><div className="pagination"><button className="glass-button" disabled={page===1} onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {page} of {Math.max(1,result.pages)}</span><button className="glass-button" disabled={page>=result.pages} onClick={()=>setPage(p=>p+1)}>Next</button></div></section>}</>;
}


