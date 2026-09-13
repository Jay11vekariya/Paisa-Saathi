# Privacy and responsible AI

Paisa Saathi is a hackathon prototype using synthetic/demo banking data. It is **designed for regulatory readiness** but does not claim RBI, DPDP, or other regulatory compliance.

## Safeguards

- **Privacy and consent:** customers can control personalized recommendations, financial insights and AI context. Production would require consent lifecycle, retention and withdrawal controls.
- **Data minimization:** each service receives only the customer data required for its purpose. Chat receives compact verified context rather than unrestricted database access.
- **Synthetic data:** demo profiles, transactions, products, anomaly scenarios and KYC values are fictional. Real identity documents are rejected and never stored by the KYC prototype.
- **JWT isolation:** authenticated identity controls customer lookup. Query strings and path parameters cannot switch a signed-in user to another customer.
- **Explainability:** health, stress, profile, recommendation, loan and anomaly results expose evidence and methodology.
- **Fairness:** recommendations use relevant financial signals—income stability, spending, savings, affordability, debt burden and stated need. Protected attributes must not drive unfair product treatment.
- **No predatory lending:** SUPPORT, HIGH and CRITICAL states prioritize stabilization and safer alternatives instead of aggressive borrowing prompts.
- **Customer control:** alerts may be read, dismissed, confirmed or reported. Prototype actions update status only and do not contact a bank.
- **Human oversight:** production credit, fraud and KYC decisions require appropriate human and institutional controls.
- **Local AI:** Ollama/Qwen runs locally. Deterministic engines remain authoritative and unsafe language-model output falls back to vetted copy.

## Prototype regulatory readiness

A production deployment would require assessment of applicable DPDP Act and RBI requirements, consent and audit systems, security and model-risk review, formal fairness testing, data-localization controls where applicable, production KYC controls, incident response, retention/deletion policy, accessibility review and human escalation.
