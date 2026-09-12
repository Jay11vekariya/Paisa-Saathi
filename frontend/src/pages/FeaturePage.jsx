import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, ArrowUpRight } from 'lucide-react';
export default function FeaturePage({ title, description, Icon, items, subtitle }) {
 return <><div className="page-heading"><div><span className="eyebrow">YOUR FINANCIAL COMPANION</span><h1>{title}</h1><p>{description}</p></div></div><section className="glass feature-hero"><div className="feature-emblem"><Icon size={44}/></div><span className="subtle-tag">COMING IN THE NEXT PHASE</span><h2>{subtitle}</h2><p>{description}</p><div className="feature-items">{items.map((item,i) => <div key={item}><span>0{i+1}</span><strong>{item}</strong><ArrowUpRight size={18}/></div>)}</div><div className="feature-foot"><span>This preview does not calculate or process financial data.</span><Link to="/dashboard"><ArrowLeft size={16}/> Back to dashboard</Link></div></section></>;
}

