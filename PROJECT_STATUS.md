# Project Status

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

Fraud detection, segmentation, loan-simulator functionality, vernacular AI, and security features remain outside this task.
