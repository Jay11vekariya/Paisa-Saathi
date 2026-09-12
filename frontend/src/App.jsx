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
export default function App() { return <DashboardProvider><Routes><Route path="/login" element={<Login/>}/><Route element={<Shell/>}><Route path="/transactions" element={<TransactionsPage/>}/><Route path="/dashboard" element={<Dashboard/>}/><Route path="/financial-health" element={<FinancialHealth/>}/><Route path="/recommendations" element={<Recommendations/>}/><Route path="/chat" element={<Chat/>}/><Route path="/security" element={<Security/>}/><Route path="/loan-simulator" element={<LoanSimulator/>}/></Route><Route path="*" element={<Navigate to="/login" replace/>}/></Routes></DashboardProvider>; }


