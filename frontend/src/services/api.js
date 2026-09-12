const base = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api').replace(/\/$/, '');
export async function request(path, options = {}) {
  const response = await fetch(`${base}${path}`, { ...options, signal: options.signal || AbortSignal.timeout(12000) });
  if (!response.ok) throw new Error('Financial data is temporarily unavailable.');
  return response.json();
}
const customerPath = (name,id) => `/${name}/${encodeURIComponent(id)}`;
export const getCustomers = options => request('/customers',options);
export const getDashboard = (id,options) => request(customerPath('dashboard',id),options);
export const getTransactions = (id,page=1,options) => request(`${customerPath('transactions',id)}?page=${page}&limit=20`,options);
export const getFinancialHealth = (id,options) => request(customerPath('financial-health',id),options);
export const getFinancialState = (id,options) => request(customerPath('financial-state',id),options);
export const getSpending = (id,options) => request(customerPath('spending',id),options);
export const api = { health: () => request('/health'), dashboard: () => request('/dashboard'), transactions: () => request('/transactions') };
