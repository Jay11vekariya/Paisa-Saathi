import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Shell from './components/layout/Shell';
import { DashboardProvider } from './hooks/useDashboard';
import TransactionsPage from './pages/Transactions';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import FinancialHealth from './pages/FinancialHealth';
import Recommendations from './pages/Recommendations';
import Chat from './pages/Chat';
import Security from './pages/Security';
import LoanSimulator from './pages/LoanSimulator';
import Register from './pages/Register';
import Onboarding from './pages/Onboarding';
import Alerts from './pages/Alerts';
import LoanJourney from './pages/LoanJourney';
import KycDemo from './pages/KycDemo';
import ResponsibleAI from './pages/ResponsibleAI';
import DemoMode from './pages/DemoMode';
const RequireAuth = ({children}) => localStorage.getItem('paisa_saathi_token') ? children : <Navigate to="/login" replace/>;
export default function App() { return <DashboardProvider><Routes><Route path="/login" element={<Login/>}/><Route path="/register" element={<Register/>}/><Route path="/onboarding" element={<RequireAuth><Onboarding/></RequireAuth>}/><Route element={<RequireAuth><Shell/></RequireAuth>}><Route path="/transactions" element={<TransactionsPage/>}/><Route path="/dashboard" element={<Dashboard/>}/><Route path="/financial-health" element={<FinancialHealth/>}/><Route path="/recommendations" element={<Recommendations/>}/><Route path="/chat" element={<Chat/>}/><Route path="/security" element={<Security/>}/><Route path="/loan-simulator" element={<LoanSimulator/>}/><Route path="/alerts" element={<Alerts/>}/><Route path="/loan-journey" element={<LoanJourney/>}/><Route path="/kyc" element={<KycDemo/>}/><Route path="/privacy" element={<ResponsibleAI/>}/><Route path="/demo" element={<DemoMode/>}/><Route path="/kyc-demo" element={<Navigate to="/kyc" replace/>}/><Route path="/responsible-ai" element={<Navigate to="/privacy" replace/>}/><Route path="/demo-mode" element={<Navigate to="/demo" replace/>}/></Route><Route path="*" element={<Navigate to="/login" replace/>}/></Routes></DashboardProvider>; }


