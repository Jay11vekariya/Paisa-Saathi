# Project Status

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
