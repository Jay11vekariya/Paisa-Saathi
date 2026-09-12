import React, { createContext, useContext, useEffect, useState } from 'react';
import { getCustomers, getDashboard } from '../services/api';
const DashboardContext = createContext(null);

export function DashboardProvider({children}) {
  const [customerId,setCustomerId] = useState('PS001');
  const [customers,setCustomers] = useState([]);
  const [dashboard,setDashboard] = useState(null);
  const [status,setStatus] = useState('loading');
  const [attempt,setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(),15000);
    setStatus('loading'); setDashboard(null);
    Promise.all([getCustomers({signal:controller.signal}),getDashboard(customerId,{signal:controller.signal})])
      .then(([list,data]) => {
        if (!data.financial_health || !data.metrics || data.customer.customer_id !== customerId || !Array.isArray(list.customers)) throw new Error('Unexpected data');
        if (active) { setCustomers(list.customers); setDashboard(data); setStatus('connected'); }
      }).catch(() => { if (active) setStatus('error'); }).finally(() => clearTimeout(timeout));
    return () => { active=false; controller.abort(); clearTimeout(timeout); };
  },[customerId,attempt]);
  const selectCustomer = id => { if (id !== customerId) { setDashboard(null);setStatus('loading');setCustomerId(id); } };
  const customer = dashboard?.customer || customers.find(c => c.customer_id === customerId);
  return React.createElement(DashboardContext.Provider, {value:{dashboard,status,customerId,customers,customer,selectCustomer,retry:()=>setAttempt(n=>n+1)}}, children);
}
export function useDashboard() { return useContext(DashboardContext); }

