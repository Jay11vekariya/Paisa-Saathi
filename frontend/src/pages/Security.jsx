import React from 'react';
import { ShieldCheck } from 'lucide-react';
import FeaturePage from './FeaturePage';
export default function Security() { return <FeaturePage title="Security Center" subtitle="A thoughtful watch over your money." description="Unusual transaction and fraud alerts will appear here. No live monitoring is active in this phase." Icon={ShieldCheck} items={['Transaction awareness','Unusual activity alerts','Clear next steps']}/>; }

