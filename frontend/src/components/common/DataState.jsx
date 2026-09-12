import React from 'react';
import { RefreshCw, CloudOff } from 'lucide-react';
export default function DataState({status,retry}) {
 if(status==='loading') return <div className="skeleton-dashboard" role="status" aria-label="Fetching financial analysis"><div className="skeleton hero-skeleton"/><div className="skeleton hero-skeleton"/>{[1,2,3,4].map(i=><div className="skeleton metric-skeleton" key={i}/>)}<div className="skeleton chart-skeleton"/><div className="skeleton chart-skeleton"/><span className="sr-only">Fetching financial analysis</span></div>;
 return <section className="glass data-error" role="alert"><span className="feature-emblem"><CloudOff size={34}/></span><h2>Financial data is temporarily unavailable.</h2><p>We couldn’t reach your financial overview. Please try again in a moment.</p><button className="glass-button" onClick={retry}><RefreshCw size={17}/> Retry</button></section>;
}
