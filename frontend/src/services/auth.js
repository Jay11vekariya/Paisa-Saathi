import { request } from './api';
export const demoLogin = () => request('/auth/demo', { method: 'POST' });
export const register = data => request('/auth/register', { method: 'POST', body: JSON.stringify(data) });
export const login = data => request('/auth/login', { method: 'POST', body: JSON.stringify(data) });
export const me = () => request('/auth/me');
export const saveProfile = data => request('/profile', { method: 'PUT', body: JSON.stringify(data) });
const notifySessionChange = () => window.dispatchEvent(new Event('paisa-saathi-auth-change'));
export const logout = () => { localStorage.removeItem('paisa_saathi_token'); localStorage.removeItem('paisa_saathi_user'); localStorage.removeItem('paisa_saathi_demo'); notifySessionChange(); };
export const saveSession = result => { localStorage.setItem('paisa_saathi_token', result.token); localStorage.setItem('paisa_saathi_user', JSON.stringify(result.user)); if(result.demo_mode&&result.scenario)localStorage.setItem('paisa_saathi_demo',JSON.stringify(result.scenario));else localStorage.removeItem('paisa_saathi_demo'); notifySessionChange(); };
