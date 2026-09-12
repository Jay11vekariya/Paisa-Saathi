import React from 'react';
import { Sparkles } from 'lucide-react';
import FeaturePage from './FeaturePage';
export default function Recommendations() { return <FeaturePage title="Recommendations" subtitle="Your needs. Your goals. Your next step." description="Personalized recommendations will appear here based on your financial state." Icon={Sparkles} items={['Understand your priorities','Explore relevant options','Plan your next milestone']}/>; }

