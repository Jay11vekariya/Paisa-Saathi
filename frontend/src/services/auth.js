import { request } from './api';
export const demoLogin = () => request('/auth/demo', { method: 'POST' });
export const register = data => request('/auth/register', { method: 'POST', body: JSON.stringify(data) });
export const login = data => request('/auth/login', { method: 'POST', body: JSON.stringify(data) });
export const me = () => request('/auth/me');
export const saveProfile = data => request('/profile', { method: 'PUT', body: JSON.stringify(data) });
const notifySessionChange = () => window.dispatchEvent(new Event('paisa-saathi-auth-change'));
export const logout = () => { localStorage.removeItem('paisa_saathi_token'); localStorage.removeItem('paisa_saathi_user'); notifySessionChange(); };
export const saveSession = result => { localStorage.setItem('paisa_saathi_token', result.token); localStorage.setItem('paisa_saathi_user', JSON.stringify(result.user)); notifySessionChange(); };
