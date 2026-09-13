# Paisa Saathi architecture

Paisa Saathi follows one product loop: **data → understanding → personalization → explanation → proactive action → customer benefit**. Financial values and decisions remain deterministic; the local language model explains verified results.

```mermaid
flowchart TB
  C[Customer] --> UI[Responsive web / mobile UI]
  UI --> R[React + Vite frontend]
  R --> API[Flask API + JWT identity]
  API --> DB[(MongoDB)]
  API --> FI[Financial intelligence layer]
  FI --> TA[Transaction analysis]
  FI --> FH[Financial health]
  FI --> FS[Financial stress]
  FI --> KM[K-Means segmentation]
  FI --> RE[Recommendation engine]
  FI --> LS[Loan impact simulator]
  FI --> AD[Anomaly detection]
  FI --> PA[Proactive intervention]
  TA & FH & FS & KM & RE & LS & AD & PA --> G[Verified compact context]
  G --> SA[Saathi AI explanation layer]
  SA --> OL[Local Ollama]
  OL --> Q[Qwen 3 1.7B<br/>English · Hindi · Gujarati]
  Q --> R
  P[Privacy · consent · explainability<br/>fairness · audit · responsible AI] -. guardrails .-> API
  P -. guardrails .-> FI
  P -. guardrails .-> SA
```

## End-to-end customer journeys

```mermaid
flowchart LR
  O[Onboarding] --> D[Customer data] --> T[Transaction analysis] --> P[Financial profile]
  P --> H[Financial health] --> S[Financial stress] --> R[Personalized recommendation] --> A[Customer action]
  T --> X[Anomaly detection] --> AL[Proactive alert] --> I[Empathetic intervention]
  Q[Customer question] --> AI[Saathi AI] --> V[Verified financial engine] --> N[Natural-language response]
```

Security boundaries: JWT identity selects one customer; URL parameters cannot switch authenticated identity; demo sessions are restricted to an allowlist of synthetic profiles; Ollama is loopback-only; KYC is a non-persistent synthetic prototype.
