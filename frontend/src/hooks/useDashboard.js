import React, { createContext, useContext, useEffect, useState } from 'react';
import { getCustomers, getDashboard, getMyDashboard } from '../services/api';
const DashboardContext = createContext(null);

export function DashboardProvider({children}) {
  const [sessionVersion,setSessionVersion] = useState(0);
  const signedIn = Boolean(localStorage.getItem('paisa_saathi_token'));
  const [customerId,setCustomerId] = useState(null);
  const [customers,setCustomers] = useState([]);
  const [dashboard,setDashboard] = useState(null);
  const [status,setStatus] = useState('loading');
  const [attempt,setAttempt] = useState(0);
  useEffect(() => {
    const refreshSession = () => { setDashboard(null); setCustomers([]); setCustomerId(null); setStatus('loading'); setSessionVersion(version => version + 1); };
    window.addEventListener('paisa-saathi-auth-change', refreshSession);
    window.addEventListener('storage', refreshSession);
    return () => { window.removeEventListener('paisa-saathi-auth-change', refreshSession); window.removeEventListener('storage', refreshSession); };
  }, []);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(),15000);
    setStatus('loading'); setDashboard(null);
    if (!signedIn) { setStatus('idle'); return () => { active=false; controller.abort(); clearTimeout(timeout); }; }
    const load = Promise.all([Promise.resolve({customers:[]}), getMyDashboard({signal:controller.signal})]);
    load.then(([list,data]) => {
        if (!data.financial_health || !data.metrics || !data.customer || !Array.isArray(list.customers)) throw new Error('Unexpected data');
        if (active) { setCustomers(list.customers); setDashboard(data); if (signedIn) setCustomerId(data.customer.customer_id); setStatus('connected'); }
      }).catch(() => { if (active) setStatus('error'); }).finally(() => clearTimeout(timeout));
    return () => { active=false; controller.abort(); clearTimeout(timeout); };
  },[attempt,signedIn,sessionVersion]);
  const selectCustomer = id => { if (id !== customerId) { setDashboard(null);setStatus('loading');setCustomerId(id); } };
  const customer = dashboard?.customer || customers.find(c => c.customer_id === customerId);
  return React.createElement(DashboardContext.Provider, {value:{dashboard,status,customerId,customers,customer,selectCustomer,retry:()=>setAttempt(n=>n+1),signedIn}}, children);
}
export function useDashboard() { return useContext(DashboardContext); }

