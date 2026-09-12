import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowDownLeft, ArrowUpRight, ShoppingBag, Utensils, Zap, Briefcase, ArrowLeftRight, CreditCard, Home, HeartPulse, Bus, GraduationCap, Film, TrendingUp } from 'lucide-react';
import { money } from '../../utils/format';
const icons={Food:Utensils,Shopping:ShoppingBag,Salary:Briefcase,Bills:Zap,EMI:CreditCard,Rent:Home,Healthcare:HeartPulse,Transport:Bus,Education:GraduationCap,Entertainment:Film,Investment:TrendingUp};
export function TransactionList({transactions}) {
 return <div className="transaction-list">{transactions.length ? transactions.map(t=>{const Icon=icons[t.category]||ArrowLeftRight;return <div className="transaction" key={t.transaction_id}><span className="transaction-icon"><Icon size={19}/></span><div className="merchant"><strong>{t.merchant}</strong><small>{t.category} <span>· {new Date(t.date+'T12:00:00').toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'2-digit'})}</span></small></div><span className={`amount ${t.type==='credit'?'positive':''}`}>{t.type==='credit'?'+':'−'}{money(t.amount)}<span className="sr-only">{t.type}</span></span>{t.type==='credit'?<ArrowDownLeft size={16} className="positive"/>:<ArrowUpRight size={16} className="muted"/>}</div>;}):<p className="empty-transactions">No transactions in this period.</p>}</div>;
}
export default function Transactions({transactions}) {
 return <section className="glass transactions"><div className="section-heading"><div><span className="eyebrow">YOUR RECENT ACTIVITY</span><h2>Little moments. Clear records.</h2></div><Link className="text-link" to="/transactions">View all <ArrowUpRight size={16}/></Link></div><TransactionList transactions={transactions}/></section>;
}
