# Project Status

## Completed: Financial stress detection

- Added a deterministic 0–100 Estimated Financial Stress indicator with LOW, MODERATE, HIGH, and CRITICAL levels.
- The documented formula uses income stability (20%), expense burden (20%), savings behaviour (15%), debt/EMI burden (15%), cash-flow surplus (15%), spending pattern (10%), and emergency buffer (5%).
- Responses contain structured factors, positive factors, guidance, data-quality metadata, and an explicit statement that this is not a credit score or lending decision.
- Added authenticated `GET /api/financial-stress` plus an identity-checked parameterized compatibility route.
- New users require at least two observed months and six transactions; onboarding baselines alone return `insufficient_data` without fabricated behaviour.

## Completed: K-Means customer segmentation

- Added actual scikit-learn K-Means clustering with four clusters, `StandardScaler`, `random_state=42`, and `n_init=20`.
- Features: income, average spending, monthly surplus, savings rate, EMI burden, income/expense stability, emergency buffer, expense change, transaction frequency, and estimated stress.
- Raw cluster IDs are mapped by centroid risk order to GROWTH, BALANCED, CAUTION, and SUPPORT; stress is dominant and savings rate is the deterministic tie-breaker.
- Model/scaler bundles are cached by a hash of training features and retrained when those features change.
- Added authenticated `GET /api/segmentation` plus an identity-checked parameterized compatibility route.

## Completed: Responsible-personalization integration

- Dashboard and Financial Health now display Liquid Glass stress and financial-profile cards, factor explanations, confidence, characteristics, and insufficient-data states.
- Recommendations display recent financial state, estimated stress, and longer-term segment together.
- The existing recommendation engine consumes both new signals. HIGH/CRITICAL stress or CAUTION/SUPPORT patterns tighten guidance while preserving “Why NOT This?” and safer alternatives.

## Completed: Authentication and new-user personalization

- Added password-hashed registration, JWT login/session identity, logout, profile onboarding, and private transaction entry.
- A new user’s stated income, expenses, EMI, and balance flow through the existing financial-health, financial-state, and recommendation engines without fabricated transactions.
- Authenticated dashboard, health, transactions, and recommendations resolve the customer from the JWT; demo customers and their scenarios remain intact.
- Added Register and onboarding screens plus in-memory tests for registration, wrong password, duplicate email, baseline analytics, private transactions, recommendations, and user isolation.
- Added an idempotent `backend/seed_demo_users.py` command. It links every existing synthetic customer to deterministic demo-only credentials and lets those accounts use the normal JWT login API and protected pages.

## Completed: Synthetic, Explainable Recommendation Engine

- Added `GET /api/recommendations/<customer_id>` for synthetic seeded customers.
- The route reuses the existing calculated dashboard metrics and financial state; it does not alter financial analytics.
- Recommendations are deterministic and explainable. Every recommendation includes a product, customer action, category, reason, `why_this`, suitability, confidence, and priority.
- Unsuitable options include `why_not_this`, the calculated customer conditions that triggered rejection, and a safer alternative action.
- Support and Caution states prioritise cash-flow education, payment review, and emergency-buffer planning. New loan and investment examples are excluded when they would add risk.
- The pure rule layer is isolated from data access, leaving a controlled extension point for future ML candidate ranking without replacing the customer-safety rules.
- The Recommendations page now loads this API and retains the existing Liquid Glass visual language.

## Verification

- Backend: `python -m unittest -v` from `backend`.
- Frontend: `npm run build` from `frontend`.

## Intentionally not implemented

Fraud/anomaly detection, loan-impact simulator functionality, vernacular/conversational AI, and production security/deployment hardening remain outside this task.
