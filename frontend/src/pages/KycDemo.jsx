import React,{useEffect,useState} from 'react';
import {ArrowLeft,ArrowRight,CheckCircle2,LayoutDashboard,ShieldCheck,UserCheck} from 'lucide-react';
import {Link} from 'react-router-dom';
import DataState from '../components/common/DataState';
import {useDashboard} from '../hooks/useDashboard';
import {completeKycDemo,getKycDemo} from '../services/api';

const guidance=[
 ['Let’s begin with your basic details.','ચાલો, તમારી basic detailsથી શરૂ કરીએ.','चलिए, आपकी basic details से शुरू करते हैं।'],
 ['Where should this demo profile be based?','તમારું demo profile ક્યાંનું છે?','आपका demo profile कहाँ का है?'],
 ['Choose a demo identity type—never enter a real number.','ફક્ત demo identity પસંદ કરો—real number ક્યારેય ન લખશો.','केवल demo identity चुनें—कभी real number न डालें।'],
 ['Review the synthetic details before completing.','પૂર્ણ કરતા પહેલાં synthetic details તપાસો.','पूरा करने से पहले synthetic details जाँचें।'],
];

export default function KycDemo(){
 const {customer}=useDashboard();
 const [config,setConfig]=useState(null),[step,setStep]=useState(0),[result,setResult]=useState(null),[error,setError]=useState(''),[attempt,setAttempt]=useState(0),[submitting,setSubmitting]=useState(false);
 const [form,setForm]=useState({full_name:'Demo Customer',date_of_birth:'1992-04-18',city:'Ahmedabad',state:'Gujarat',pincode:'380001',identity_type:'',demo_reference:''});
 useEffect(()=>{let active=true;const controller=new AbortController();setError('');getKycDemo({signal:controller.signal}).then(data=>{if(active){setConfig(data);setForm(current=>({...current,full_name:customer?.name||current.full_name,city:customer?.city||current.city,identity_type:data.identity_types[0],demo_reference:data.masked_demo_id}))}}).catch(err=>{if(active)setError(err.message)});return()=>{active=false;controller.abort()}},[attempt,customer?.name,customer?.city]);
 const update=e=>setForm(current=>({...current,[e.target.name]:e.target.value}));
 const next=e=>{e.preventDefault();if(e.currentTarget.reportValidity())setStep(value=>Math.min(value+1,3))};
 const submit=async()=>{setError('');setSubmitting(true);try{setResult(await completeKycDemo(form))}catch(err){setError(err.message)}finally{setSubmitting(false)}};
 if(!config)return <DataState status={error?'error':'loading'} retry={()=>setAttempt(value=>value+1)}/>;
 if(result)return <section className="glass kyc-complete"><CheckCircle2/><span className="eyebrow">DEMO KYC COMPLETE</span><h1>{result.status}</h1><p>No real identity data was collected, stored, or government-verified.</p><div><Link className="primary-button" to="/dashboard"><LayoutDashboard size={16}/>Back to Dashboard</Link><Link to="/privacy"><ShieldCheck size={16}/>Review privacy safeguards</Link></div></section>;
 return <><div className="page-heading"><div><span className="eyebrow">DEMO / PROTOTYPE</span><h1>KYC with Saathi</h1><p>Complete your basic banking profile with a guided conversation.</p></div><UserCheck/></div><div className="prototype-banner">DEMO MODE · Never enter a real Aadhaar, PAN, identity number, biometric, or document.</div><div className="journey-progress kyc-progress">{config.steps.map((label,index)=><span className={index<=step?'active':''} key={label}>{index+1} {label}</span>)}</div><section className="glass kyc-card"><div className="kyc-guide"><span className="eyebrow">SAATHI GUIDANCE · STEP {step+1} OF 4</span><h2>{guidance[step][0]}</h2><p>{guidance[step][1]}<br/>{guidance[step][2]}</p><div className="demo-id"><small>SYNTHETIC DEMO VALUE</small><strong>{config.masked_demo_id}</strong></div><p className="kyc-notice"><ShieldCheck size={16}/>{config.notice}</p></div><form onSubmit={next}>
 {step===0&&<><label>Full name<input name="full_name" value={form.full_name} onChange={update} required/></label><label>Date of birth<input name="date_of_birth" type="date" value={form.date_of_birth} onChange={update} required/></label></>}
 {step===1&&<><label>City<input name="city" value={form.city} onChange={update} required/></label><label>State<input name="state" value={form.state} onChange={update} required/></label><label>PIN code<input name="pincode" inputMode="numeric" pattern="[0-9]{6}" maxLength="6" value={form.pincode} onChange={update} required/></label></>}
 {step===2&&<><label>Demo identity type<select name="identity_type" value={form.identity_type} onChange={update}>{config.identity_types.map(item=><option key={item}>{item}</option>)}</select></label><label>Masked demo reference<input name="demo_reference" value={form.demo_reference} readOnly/></label><p className="demo-disclaimer">This value is synthetic and cannot be replaced with a real identity number.</p></>}
 {step===3&&<div className="kyc-review">{[['Name',form.full_name],['Date of birth',form.date_of_birth],['Location',`${form.city}, ${form.state} · ${form.pincode}`],['Identity type',form.identity_type],['Demo reference',form.demo_reference]].map(([label,value])=><div key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>}
 <div className="kyc-buttons">{step>0&&<button type="button" onClick={()=>setStep(value=>value-1)}><ArrowLeft size={16}/>Back</button>}{step<3?<button className="primary-button">Continue<ArrowRight size={16}/></button>:<button type="button" className="primary-button" disabled={submitting} onClick={submit}>{submitting?'Completing…':'Complete demo KYC'}<CheckCircle2 size={16}/></button>}</div>{error&&<p className="form-message">{error}</p>}</form></section><p className="demo-disclaimer">Synthetic fields are processed only for this response and are not stored.</p></>;
}
