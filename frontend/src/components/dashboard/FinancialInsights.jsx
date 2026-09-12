import React from 'react';
import { Activity, ArrowUpRight, BrainCircuit, Check, TriangleAlert } from 'lucide-react';
import { Link } from 'react-router-dom';

export function StressCard({ stress, detailed = false }) {
  const available = stress?.status === 'available';
  const tone = stress?.stress_level?.toLowerCase() || 'unknown';
  return <section className={`glass insight-card stress-card stress-${tone}`}>
    <div className="insight-card-top"><span className="round-icon"><Activity size={20}/></span><span className="eyebrow">ESTIMATED FINANCIAL STRESS</span>{!detailed && <Link to="/financial-health" aria-label="View stress details"><ArrowUpRight size={18}/></Link>}</div>
    {available ? <><div className="insight-score"><strong>{stress.stress_score}</strong><span>/ 100</span><b>{stress.stress_level}</b></div><div className="stress-meter" aria-label={`Estimated financial stress ${stress.stress_score} out of 100`}><span style={{width:`${stress.stress_score}%`}}/></div>{detailed ? <div className="stress-factor-grid">{stress.factors.map(factor => <div className="stress-factor" key={factor.key}><span className={factor.impact}><i/>{factor.name}</span><strong>{factor.value}</strong><small>{factor.explanation}</small><em>{factor.points.toFixed(1)} / {factor.weight} stress points</em></div>)}</div> : <p>{stress.guidance[0]}</p>}</> : <div className="insufficient-insight"><strong>Insufficient data</strong><p>{stress?.guidance?.[0] || 'We need more transaction history to estimate your financial stress.'}</p></div>}
    <small className="insight-disclaimer">Prototype indicator · Not a credit score</small>
  </section>;
}

export function SegmentCard({ segmentation, detailed = false }) {
  const available = segmentation?.status === 'available';
  return <section className="glass insight-card segment-card">
    <div className="insight-card-top"><span className="round-icon"><BrainCircuit size={20}/></span><span className="eyebrow">YOUR FINANCIAL PROFILE</span>{!detailed && <Link to="/financial-health" aria-label="View profile details"><ArrowUpRight size={18}/></Link>}</div>
    {available ? <><div className="segment-heading"><span>LONGER-TERM PATTERN</span><strong>{segmentation.segment}</strong><small>{segmentation.confidence} confidence</small></div><p>{segmentation.segment_description}</p><div className="characteristics">{segmentation.key_characteristics.map(item => <div key={item.text} className={item.impact}><span>{item.impact === 'positive' ? <Check size={14}/> : <TriangleAlert size={14}/>}</span>{item.text}</div>)}</div>{detailed && <div className="how-we-know"><strong>How we know</strong><p>We compare verified financial-behaviour patterns using four reproducible groups. Your recent financial state can differ from this longer-term profile.</p></div>}</> : <div className="insufficient-insight"><strong>Not enough data</strong><p>{segmentation?.segment_description || 'We need more transaction history to estimate your financial behaviour.'}</p></div>}
    <small className="insight-disclaimer">Pattern grouping · No lending eligibility decision</small>
  </section>;
}

export default function FinancialInsights({ stress, segmentation, detailed = false }) {
  return <div className={`financial-insights ${detailed ? 'financial-insights-detailed' : ''}`}><StressCard stress={stress} detailed={detailed}/><SegmentCard segmentation={segmentation} detailed={detailed}/></div>;
}
