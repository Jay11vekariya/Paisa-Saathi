"""Static product safeguards and allowlisted demo/KYC metadata."""

DEMO_SCENARIOS = {
    'rahul-growth': {'customer_id': 'PS001', 'name': 'Rahul', 'tone': 'GREEN', 'title': 'Healthy Financial Profile',
                     'profile': 'GROWTH', 'summary': 'Low stress · Strong savings', 'start_path': '/dashboard'},
    'ramesh-stress': {'customer_id': 'PS003', 'name': 'Ramesh', 'tone': 'ORANGE', 'title': 'Financial Stress',
                      'profile': 'CAUTION', 'summary': 'High stress · Negative surplus', 'start_path': '/dashboard'},
    'aman-fraud': {'customer_id': 'PS004', 'name': 'Aman', 'tone': 'RED', 'title': 'Fraud / Anomaly',
                   'profile': 'SUPPORT', 'summary': 'Synthetic unusual transaction', 'start_path': '/alerts',
                   'demo_scenario': 'fraud'},
    'ramesh-gujarati': {'customer_id': 'PS003', 'name': 'Ramesh', 'tone': 'BLUE', 'title': 'Vernacular Banking',
                        'profile': 'GUJARATI', 'summary': 'Gujarati Saathi experience', 'start_path': '/chat'},
}

PRIVACY = {
    'prototype_notice': 'This prototype uses synthetic/demo banking data. Production deployment would require applicable regulatory controls.',
    'data_used': ['Transactions', 'Spending patterns', 'Financial behaviour', 'Customer preferences'],
    'purpose': 'To provide personalized financial guidance.',
    'controls': {'personalized_recommendations': True, 'financial_insights': True, 'ai_assistant_context': True},
}

RESPONSIBLE_AI = {
    'principles': [
        {'name': 'CUSTOMER FIRST', 'detail': 'Recommendations prioritize financial wellbeing, not product sales.'},
        {'name': 'EXPLAINABLE', 'detail': 'Every major recommendation is linked to verified evidence.'},
        {'name': 'NO PREDATORY NUDGING', 'detail': 'Customers under financial stress are not aggressively pushed toward borrowing.'},
        {'name': 'HUMAN CONTROL', 'detail': 'Customers can review, dismiss, or question recommendations and alerts.'},
        {'name': 'DATA MINIMIZATION', 'detail': 'Only information necessary for the intended guidance should be used.'},
    ],
    'fairness_guardrails': ['Income stability', 'Spending behaviour', 'Savings', 'Debt burden', 'Affordability', 'Stated financial needs'],
    'fairness_note': 'Protected or sensitive attributes must not be used for unfair product recommendations. This is a prototype safeguard; production systems require formal fairness testing.',
    'regulatory_readiness': ['Consent management', 'Data minimization', 'Audit logging', 'Customer control',
                             'Applicable DPDP Act requirements', 'Applicable RBI requirements',
                             'Data localization where applicable', 'Security review', 'Production KYC requirements'],
    'claim': 'Designed for regulatory readiness; this prototype does not claim regulatory compliance.',
}

KYC_DEMO = {
    'demo': True, 'title': 'KYC with Saathi',
    'notice': 'DEMO / PROTOTYPE — no real identity documents or identity numbers are collected or stored.',
    'steps': ['Personal details', 'Address', 'Identity information', 'Review'],
    'identity_types': ['Aadhaar (Demo)', 'PAN (Demo)', 'Other'],
    'masked_demo_id': 'XXXX-XXXX-1234',
}
