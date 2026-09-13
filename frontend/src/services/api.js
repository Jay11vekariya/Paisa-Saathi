const base = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api').replace(/\/$/, '');
export async function request(path, options = {}) {
  const token = localStorage.getItem('paisa_saathi_token');
  const headers = { ...(options.headers || {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  if (options.body) headers['Content-Type'] = 'application/json';
  const response = await fetch(`${base}${path}`, { ...options, headers, signal: options.signal || AbortSignal.timeout(12000) });
  if (!response.ok) { const data = await response.json().catch(() => ({})); if (response.status === 401) { localStorage.removeItem('paisa_saathi_token'); localStorage.removeItem('paisa_saathi_user'); window.dispatchEvent(new Event('paisa-saathi-auth-change')); } throw new Error(data.error || 'Financial data is temporarily unavailable.'); }
  return response.json();
}
const customerPath = (name,id) => `/${name}/${encodeURIComponent(id)}`;
export const getCustomers = options => request('/customers',options);
export const getDashboard = (id,options) => request(customerPath('dashboard',id),options);
export const getTransactions = (id,page=1,options) => request(`${customerPath('transactions',id)}?page=${page}&limit=20`,options);
export const getMyTransactions = (page=1,options) => request(`/transactions?page=${page}&limit=20`,options);
export const createMyTransaction = data => request('/transactions', { method:'POST', body:JSON.stringify(data) });
export const getFinancialHealth = (id,options) => request(customerPath('financial-health',id),options);
export const getFinancialState = (id,options) => request(customerPath('financial-state',id),options);
export const getSpending = (id,options) => request(customerPath('spending',id),options);
export const getRecommendations = (id,options) => request(customerPath('recommendations',id),options);
export const getMyDashboard = options => request('/dashboard', options);
export const getMyRecommendations = options => request('/recommendations', options);
export const getFinancialStress = options => request('/financial-stress', options);
export const getSegmentation = options => request('/segmentation', options);
export const getAnomalies = options => request('/anomalies', options);
export const simulateLoan = (data,options={}) => request('/loan-simulator', { ...options, method:'POST', body:JSON.stringify(data) });
export const sendChatMessage = (message,conversation_context=[],options={}) => request('/chat', { ...options, signal:options.signal||AbortSignal.timeout(165000), method:'POST', body:JSON.stringify({message,conversation_context}) });
export const getAlerts = options => request('/alerts', options);
export const updateAlert = (id,action) => request(`/alerts/${encodeURIComponent(id)}/${action}`, {method:'POST'});
export const startLoanJourney = options => request('/loan-journey/start', {method:'POST', ...options});
export const assessLoanJourney = data => request('/loan-journey/assessment', {method:'POST', body:JSON.stringify(data)});
export const getKycDemo = options => request('/kyc/demo', options);
export const completeKycDemo = data => request('/kyc/demo/complete', {method:'POST', body:JSON.stringify(data)});
export const getPrivacy = options => request('/privacy', options);
export const updatePrivacy = data => request('/privacy', {method:'PUT', body:JSON.stringify(data)});
export const getResponsibleAI = options => request('/responsible-ai', options);
export const getDemoScenarios = options => request('/demo/scenarios', options);
export const launchDemoScenario = scenario_id => request('/demo/session', {method:'POST', body:JSON.stringify({scenario_id})});
export const resetDemo = () => request('/demo/reset', {method:'POST'});
export const api = { health: () => request('/health'), dashboard: () => request('/dashboard'), transactions: () => request('/transactions') };
