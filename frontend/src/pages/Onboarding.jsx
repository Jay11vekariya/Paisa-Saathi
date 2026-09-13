import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Brand from '../components/ui/Brand';
import { saveProfile } from '../services/auth';
import { createMyTransaction } from '../services/api';

export default function Onboarding() {
  const [message, setMessage] = useState('');
  const navigate = useNavigate();
  const submit = async event => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    for (const key of ['age','monthly_income','monthly_expenses','account_balance','monthly_emi']) data[key] = Number(data[key]);
    try {
      await saveProfile(data);
      if (data.transaction_amount) await createMyTransaction({ date:data.transaction_date, type:data.transaction_type, category:data.transaction_category, amount:Number(data.transaction_amount), merchant:data.transaction_merchant, location:data.transaction_location });
      navigate('/dashboard');
    } catch (error) { setMessage(error.message); }
  };
  return <div className="login-page"><section className="login-story"><Brand/><div className="login-intro"><span className="eyebrow">STEPS 2–4 OF 4</span><h1>Make it<br/><em>personal.</em></h1><p>Your first overview uses this baseline. You can add a transaction now or skip it.</p></div></section><section className="login-form-side"><div className="glass login-card"><span className="eyebrow">YOUR PROFILE</span><h2>A clear starting point.</h2><form onSubmit={submit}>
    <label>Full name</label><input name="full_name" required/><label>Age</label><input name="age" type="number" min="18" required/><label>City</label><input name="city" required/>
    <label>Preferred language</label><select name="language"><option>English</option><option>Hindi</option><option>Gujarati</option><option>Hinglish</option></select>
    <label>What would you like Saathi to help with?</label><select name="primary_banking_need"><option>Save</option><option>Borrow</option><option>Invest</option><option>Manage expenses</option><option>Protect finances</option></select>
    <label>Primary financial goal</label><select name="financial_goals"><option>Build emergency fund</option><option>Reduce debt</option><option>Save for education</option><option>Buy a home</option><option>Grow wealth</option></select>
    <label>Employment type</label><select name="employment_type"><option>Salaried</option><option>Self-employed</option><option>Business owner</option><option>Student</option><option>Retired</option><option>Other</option></select>
    <label>Monthly income (₹)</label><input name="monthly_income" type="number" min="1" required/><label>Approximate monthly expenses (₹)</label><input name="monthly_expenses" type="number" min="0" required/><label>Current account balance (₹)</label><input name="account_balance" type="number" min="0" required/><label>Monthly EMI (₹, optional)</label><input name="monthly_emi" type="number" min="0" defaultValue="0" required/>
    <hr/><span className="eyebrow">OPTIONAL: FIRST TRANSACTION</span><label>Date</label><input name="transaction_date" type="date"/><label>Type</label><select name="transaction_type"><option value="expense">Expense</option><option value="income">Income</option></select><label>Category</label><select name="transaction_category"><option>Food</option><option>Salary</option><option>Transport</option><option>Bills</option><option>Shopping</option><option>Other</option></select><label>Amount (₹)</label><input name="transaction_amount" type="number" min="1"/><label>Merchant / Payee (optional)</label><input name="transaction_merchant" placeholder="e.g. Swiggy, employer, local store"/><label>Location (optional)</label><input name="transaction_location" placeholder="e.g. Rajkot"/>
    <button className="primary-button">Your Paisa Saathi profile is ready</button>{message && <p className="form-message">{message}</p>}
  </form><p className="login-note">Merchant means who you paid or received money from. Leave the optional transaction blank to use only your financial baseline.</p></div></section></div>;
}
