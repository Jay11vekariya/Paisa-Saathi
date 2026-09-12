import React from 'react';
import { ChevronDown, UsersRound } from 'lucide-react';
import { useDashboard } from '../../hooks/useDashboard';
export default function CustomerSwitcher() {
 const {customers,customerId,selectCustomer} = useDashboard();
 return <div className="customer-switcher"><UsersRound size={17}/><div><label htmlFor="customer-select">SYNTHETIC PROFILE</label><select id="customer-select" value={customerId} onChange={e=>selectCustomer(e.target.value)} disabled={!customers.length}>{customers.length ? customers.map(c=><option value={c.customer_id} key={c.customer_id}>{c.name}</option>) : <option value={customerId}>Connecting…</option>}</select></div><ChevronDown size={16}/></div>;
}
