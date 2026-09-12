import { request } from './api';
// Demo navigation grants no authenticated identity or access to private data.
export const demoLogin = () => request('/auth/demo', { method: 'POST' });
