import React, { useState } from 'react';
import { Info, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import GlassModal from '../ui/GlassModal';
export function FactorList({health}) {
 return <div className="factor-list">{health.factors.map(f=><div className="factor" key={f.key}><div className="factor-heading"><strong>{f.label}</strong><span>{f.weight}% weight <b>{f.contribution.toFixed(1)} / {f.weight} pts</b></span></div><div className="factor-track"><span style={{width:`${f.score}%`}}/></div><p>{f.explanation}</p></div>)}</div>;
}
export default function FinancialHealthCard({health}) {
 const [explain,setExplain] = useState(false);
 const circumference = 2*Math.PI*76;
 return <section className="glass wellness-hero"><div className="section-heading"><span className="eyebrow">FINANCIAL HEALTH</span><Link to="/financial-health" className="icon-button" aria-label="View full financial health analysis"><ArrowUpRight size={20}/></Link></div><div className="score-visual"><svg viewBox="0 0 190 190" role="img" aria-label={`Wellness score ${health.score} out of 100, ${health.status}`}><circle cx="95" cy="95" r="86" className="score-orbit"/><circle cx="95" cy="95" r="76" className="score-track"/><circle cx="95" cy="95" r="76" className="score-progress" strokeDasharray={circumference} strokeDashoffset={circumference*(1-health.score/100)} transform="rotate(-90 95 95)"/></svg><div className="score-value"><strong>{health.score}</strong><span>out of 100</span><b>{health.status}</b></div></div><div className="score-caption"><span>Income</span><i/><span>Savings</span><i/><span>Debt</span><i/><span>Buffer</span></div><button className="explain-button" onClick={()=>setExplain(true)}><Info size={15}/> How is this calculated?</button><small className="wellness-note">Prototype wellness score · Not a credit score</small>{explain && <GlassModal title="The story behind your score" onClose={()=>setExplain(false)}><p className="modal-intro">Five transparent factors add up to {health.score}/100. Each factor’s points equal its score × weight; the total is rounded.</p><FactorList health={health}/><p className="modal-disclaimer">{health.methodology}</p></GlassModal>}</section>;
}
