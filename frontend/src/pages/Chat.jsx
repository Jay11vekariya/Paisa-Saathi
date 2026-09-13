import React,{useEffect,useRef,useState} from 'react';
import {Bell,Bot,HeartPulse,Landmark,LockKeyhole,MessageCircle,ReceiptText,RefreshCw,Send,ShieldAlert,Sparkles,User,UserCheck} from 'lucide-react';
import {Link} from 'react-router-dom';
import {sendChatMessage} from '../services/api';
import {useDashboard} from '../hooks/useDashboard';

const starters=[
 {label:'Check health',message:'How is my financial health?',Icon:HeartPulse},
 {label:'Check spending',message:'Where am I spending the most?',Icon:ReceiptText},
 {label:'Explore a loan',message:'I want to understand a loan impact.',Icon:Landmark},
 {label:'View alerts',message:'Do I have any Saathi alerts?',Icon:Bell},
 {label:'Explain fraud flag',message:'Why was this transaction flagged?',Icon:ShieldAlert},
 {label:'KYC guidance',message:'Help me with KYC.',Icon:UserCheck},
 {label:'Privacy controls',message:'How is my data used?',Icon:LockKeyhole},
];

export default function Chat(){
 const {customer}=useDashboard();
 const [messages,setMessages]=useState([{role:'assistant',welcome:true,content:'Namaste! I’m Paisa Saathi. Ask me about your financial health, spending, loan impact, or unusual activity—in English, ગુજરાતી, or हिंदी.'}]);
 const [text,setText]=useState(''),[sending,setSending]=useState(false),[failed,setFailed]=useState(null);
 const endRef=useRef(null),inputRef=useRef(null);
 useEffect(()=>{
  endRef.current?.scrollIntoView({behavior:'smooth'});
 },[messages,sending]);
 const send=async value=>{
  const message=(value??text).trim();if(!message||sending)return;
  const context=messages.filter(item=>!item.welcome).slice(-8).map(({role,content})=>({role,content}));
  setMessages(items=>[...items,{role:'user',content:message}]);setText('');setSending(true);setFailed(null);
  try{const result=await sendChatMessage(message,context);setMessages(items=>[...items,{role:'assistant',content:result.assistant_message,language:result.detected_language,fallback:result.fallback,provider:result.provider,actions:result.actions||[],intentCode:result.intent_code}]);}
  catch(error){setFailed({message,error:error.message});}
  finally{setSending(false);inputRef.current?.focus()}
 };
 const keyDown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}};
 return <div className="chat-page"><div className="page-heading"><div><span className="eyebrow">VERNACULAR BANKING COMPANION</span><h1>Talk to Paisa Saathi</h1><p>Grounded explanations from {customer?.name||'your'} verified financial context.</p></div><MessageCircle/></div>
  <section className="glass chat-shell">
   <header className="chat-assistant"><span className="saathi-avatar"><Sparkles size={20}/></span><div><strong>Paisa Saathi</strong><small><i/> Ready in English · ગુજરાતી · हिंदी</small></div></header>
   <div className="chat-messages" aria-live="polite">{messages.map((item,index)=><div className={`chat-row ${item.role}`} key={`${index}-${item.content.slice(0,12)}`}><span className="message-avatar">{item.role==='assistant'?<Bot size={17}/>:<User size={17}/>}</span><div className="message-bubble"><p>{item.content}</p>{item.actions?.length>0&&<div className="chat-actions">{item.actions.map(action=><Link key={action.path} to={action.path}>{action.label}</Link>)}</div>}{item.language&&<small>{item.language}{item.fallback?' · offline-safe fallback':item.provider==='Ollama'?' · Local AI':''}{item.intentCode?` · ${item.intentCode.replaceAll('_',' ').toLowerCase()}`:''}</small>}</div></div>)}
    {sending&&<div className="chat-row assistant"><span className="message-avatar"><Bot size={17}/></span><div className="message-bubble typing" aria-label="Paisa Saathi is typing"><i/><i/><i/></div></div>}
    {failed&&<div className="chat-error"><span>{failed.error}</span><button onClick={()=>send(failed.message)}><RefreshCw size={14}/>Retry</button></div>}<div ref={endRef}/>
   </div>
   <div className="starter-prompts" aria-label="Quick questions">{starters.map(({label,message,Icon})=><button key={label} onClick={()=>send(message)} disabled={sending}><Icon size={14}/>{label}</button>)}</div>
   <div className="chat-compose"><textarea ref={inputRef} rows="1" maxLength="2000" value={text} onChange={e=>setText(e.target.value)} onKeyDown={keyDown} placeholder="Ask about your money…" aria-label="Message Paisa Saathi"/><button onClick={()=>send()} disabled={!text.trim()||sending} aria-label="Send message"><Send size={18}/></button></div>
   <footer className="chat-note">Personalized facts come from verified Paisa Saathi calculations. Guidance is educational, not an approval or eligibility decision.</footer>
  </section>
 </div>;
}
