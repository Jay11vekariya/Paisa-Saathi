import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
export default function GlassModal({title,children,onClose}) {
  const ref=useRef(null);
  useEffect(()=>{
    const dialog=ref.current, opener=document.activeElement;
    dialog.showModal();
    return()=>{if(dialog.open) dialog.close(); if(opener instanceof HTMLElement && document.contains(opener)) opener.focus();};
  },[]);
  return <dialog className="glass-modal" ref={ref} onCancel={onClose} onClick={e=>{if(e.target===ref.current) onClose();}} aria-labelledby="modal-title"><div className="modal-heading"><div><span className="eyebrow">TRANSPARENT BY DESIGN</span><h2 id="modal-title">{title}</h2></div><button className="icon-button" aria-label="Close explanation" onClick={onClose}><X/></button></div>{children}</dialog>;
}
