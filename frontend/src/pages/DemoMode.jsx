import React,{useEffect,useState} from 'react';
import {PlayCircle,RotateCcw} from 'lucide-react';
import {useNavigate} from 'react-router-dom';
import DataState from '../components/common/DataState';
import {getDemoScenarios,launchDemoScenario,resetDemo} from '../services/api';
import {saveSession} from '../services/auth';

export default function DemoMode(){
 const [data,setData]=useState(null),[message,setMessage]=useState(''),[attempt,setAttempt]=useState(0);const navigate=useNavigate();
 useEffect(()=>{let active=true;const controller=new AbortController();setMessage('');getDemoScenarios({signal:controller.signal}).then(value=>{if(active)setData(value)}).catch(err=>{if(active)setMessage(err.message)});return()=>{active=false;controller.abort()}},[attempt]);
 const launch=async scenario_id=>{try{const result=await launchDemoScenario(scenario_id);saveSession(result);navigate(result.scenario.start_path)}catch(err){setMessage(err.message)}};
 const reset=async()=>{try{await resetDemo();localStorage.removeItem('paisa_saathi_demo');setMessage('Demo actions reset. Synthetic financial data was unchanged.')}catch(err){setMessage(err.message)}};
 return <><div className="page-heading"><div><span className="eyebrow">JUDGE SCENARIO LAUNCHER</span><h1>Demo Mode</h1><p>Explore Paisa Saathi’s personalized banking scenarios.</p></div><PlayCircle/></div><div className="prototype-banner">DEMO MODE · Synthetic profiles only · Normal JWT isolation remains active.</div>{!data?<DataState status={message?'error':'loading'} retry={()=>setAttempt(value=>value+1)}/>:data.scenarios.length?<section className="demo-grid">{data.scenarios.map(item=><article className={`glass demo-scenario tone-${item.tone.toLowerCase()}`} key={item.scenario_id}><span className="scenario-dot"/><small>{item.title}</small><h2>{item.name}</h2><strong>{item.profile}</strong><p>{item.summary}</p><button onClick={()=>launch(item.scenario_id)}>Launch scenario <PlayCircle size={16}/></button></article>)}</section>:<section className="glass alert-empty"><strong>No demo scenarios available</strong><p>The allowlisted synthetic scenario catalogue is empty.</p></section>}<button className="reset-demo" onClick={reset}><RotateCcw size={16}/>Reset Demo</button>{data&&message&&<p className="form-message">{message}</p>}<p className="demo-disclaimer">Scenario tokens can access only their allowlisted synthetic customer. Demo passwords are never included in frontend code.</p></>;
}
