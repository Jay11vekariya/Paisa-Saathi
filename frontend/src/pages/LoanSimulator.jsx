import React from 'react';
import { Calculator } from 'lucide-react';
import FeaturePage from './FeaturePage';
export default function LoanSimulator() { return <FeaturePage title="Loan Simulator" subtitle="See the bigger picture before you borrow." description="Compare loan amounts, EMI and financial impact here in a future phase." Icon={Calculator} items={['Explore loan scenarios','Understand monthly EMI','Preview your financial impact']}/>; }

