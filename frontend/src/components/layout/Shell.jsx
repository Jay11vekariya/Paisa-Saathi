import React, { useState, useEffect, useRef } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { LayoutDashboard, HeartPulse, Sparkles, MessageCircle, ShieldCheck, Calculator, Bell, Menu, X, Globe, Settings, LogOut, ChevronDown } from 'lucide-react';
import Brand from '../ui/Brand';
import { useDashboard } from '../../hooks/useDashboard';
import { logout } from '../../services/auth';

export const navigation = [
  ['/dashboard','Dashboard',LayoutDashboard], ['/financial-health','Financial Health',HeartPulse],
  ['/recommendations','Recommendations',Sparkles], ['/chat','Saathi AI',MessageCircle],
  ['/security','Security Center',ShieldCheck], ['/loan-simulator','Loan Simulator',Calculator],
];

export default function Shell() {
  const [open,setOpen] = useState(false), [panel,setPanel] = useState('');
  const { customer, status, dashboard, signedIn } = useDashboard();
  const location = useLocation(), menuRef = useRef(null), triggerRef = useRef(null);
  const title = navigation.find(([path]) => path === location.pathname)?.[1] || 'Transactions';
  const initials = customer ? customer.name.split(' ').map(n=>n[0]).join('').slice(0,2) : 'PS';
  useEffect(() => {
    if (!open) return;
    const items = () => Array.from(menuRef.current.querySelectorAll('a,button')).filter(el=>el.getClientRects().length);
    items()[0]?.focus();
    const handler = e => {
      if (e.key==='Escape') { setOpen(false); triggerRef.current?.focus(); }
      if (e.key==='Tab') {
        const elements=items(), first=elements[0], last=elements[elements.length-1];
        if(e.shiftKey && document.activeElement===first) { e.preventDefault(); last.focus(); }
        else if(!e.shiftKey && document.activeElement===last) { e.preventDefault(); first.focus(); }
      }
    };
    const prior=document.body.style.overflow;
    document.body.style.overflow='hidden'; document.addEventListener('keydown',handler);
    return () => { document.body.style.overflow=prior; document.removeEventListener('keydown',handler); };
  },[open]);
  const closeMenu = () => { setOpen(false); triggerRef.current?.focus(); };
  return <div className="app-shell">
    <a href="#main-content" className="skip-link">Skip to content</a>
    {open && <button className="scrim" aria-label="Close navigation" onClick={closeMenu}/>}
    <aside ref={menuRef} className={`sidebar ${open?'is-open':''}`} aria-label="Main navigation">
      <Brand/><button className="mobile-close icon-button" aria-label="Close navigation" onClick={closeMenu}><X/></button>
      <div className="nav-label">YOUR FINANCIAL SPACE</div>
      <nav>{navigation.map(([path,label,Icon]) => <NavLink to={path} key={path} onClick={()=>setOpen(false)}><Icon size={19}/><span>{label}</span>{path==='/chat' && <small className="ai-label">SOON</small>}</NavLink>)}</nav>
      <div className="sidebar-bottom">
        <div className="companion-note"><Sparkles size={21}/><strong>Understand first.<br/>Move forward with clarity.</strong><p>Your Money, Your Needs,<br/>Your Saathi.</p></div>
        <div className="sidebar-protection"><ShieldCheck size={14}/><span>{signedIn ? 'Private profile' : 'Synthetic profile'}</span></div>
        <button className="language" onClick={()=>setPanel(panel==='language'?'':'language')}><Globe size={16}/>{customer?.language || 'Language'}<ChevronDown size={14}/></button>
        <div className="sidebar-user"><span className="avatar">{initials}</span><div><strong>{customer?.name || 'Your financial space'}</strong><small>{customer?.city || 'Phase 2 preview'}</small></div><button className="icon-button" aria-label="Settings" onClick={()=>setPanel(panel==='settings'?'':'settings')}><Settings size={18}/></button></div>
      </div>
    </aside>
    <div className="workspace">
      <header className="topbar"><div className="header-left"><button ref={triggerRef} className="menu-button icon-button" aria-label="Open navigation" aria-expanded={open} onClick={()=>setOpen(true)}><Menu/></button><span>Personal banking</span><span className="breadcrumb">/</span><strong>{title}</strong></div>
        <div className="header-right"><span className="demo-pill">{dashboard?.source === 'test-fixture' ? 'UI test fixture' : 'Phase 2 · Synthetic'}</span><button className="language-control" aria-label="Language information" onClick={()=>setPanel(panel==='language'?'':'language')}><Globe size={16}/><span>ગુજરાતી</span></button><button className="icon-button notification" aria-label="Notifications" onClick={()=>setPanel(panel==='notifications'?'':'notifications')}><Bell size={19}/></button><button className="avatar small" aria-label="Profile settings" onClick={()=>setPanel(panel==='settings'?'':'settings')}>{initials}</button></div>
      </header>
      {panel && <div className="popover" role="region" aria-label="Account information"><button className="icon-button" aria-label="Close panel" onClick={()=>setPanel('')}><X size={16}/></button><strong>{panel==='notifications'?'A quieter kind of banking':panel==='language'?'Made for Bharat':signedIn?'Your private profile':'Your synthetic profile'}</strong><p>{panel==='notifications'?'There are no live notifications. Security monitoring is planned for a later phase.':panel==='language'?'English, Hindi, Gujarati, and Hinglish can be selected in your profile.':`${customer?.name || 'This profile'} uses ${signedIn?'your onboarding baseline and transactions.':'fictional data.'}`}</p>{panel==='settings' && <NavLink to="/login" onClick={()=>{logout();setPanel('')}}><LogOut size={16}/> Log out</NavLink>}</div>}
      <main id="main-content" tabIndex={-1}>{dashboard?.source === 'test-fixture' && <div className="test-notice" role="status">UI verification fixture · No Atlas connection</div>}<Outlet/></main>
      <footer><span>PAISA SAATHI <b>·</b> Made for Bharat</span><span>Quantum Crew <b>·</b> Jay Vekariya & Megh Joshi</span></footer>
    </div>
  </div>;
}



