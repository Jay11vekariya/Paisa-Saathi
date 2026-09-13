# AI and ML approach

Paisa Saathi separates calculation from conversation. The financial layer produces auditable facts; local Qwen turns only those facts into concise English, Hindi, or Gujarati explanations.

## 1. Transaction analytics

- **Input:** authenticated customer ledger, categories, dates, credits, debits and merchants.
- **Processing:** completed-month totals, trends, spending mix and cash-flow reconciliation.
- **Output:** income, expenses, savings, EMI and behavioural signals.
- **Useful:** converts a transaction list into an understandable financial picture.
- **Safe:** calculations use one JWT-selected customer and expose their own evidence only.

## 2. Financial health scoring

- **Input:** cash flow, savings rate, EMI burden, balance and emergency buffer.
- **Processing:** transparent bounded factor scoring.
- **Output:** score, status, factor contributions and methodology.
- **Useful:** summarizes wellbeing while preserving the underlying reasons.
- **Safe:** it is a wellness indicator, not a bureau credit score or approval decision.

## 3. Financial stress detection

- **Input:** income disruption, expense pressure, savings decline, EMI burden and buffer.
- **Processing:** deterministic weighted signals with explicit thresholds.
- **Output:** LOW to CRITICAL stress, score and contributing evidence.
- **Useful:** enables early supportive intervention.
- **Safe:** HIGH/CRITICAL states prioritize stabilization over borrowing or sales.

## 4. K-Means segmentation

- **Input:** normalized financial behaviour features from synthetic customer histories.
- **Processing:** scikit-learn scaling and K-Means clustering, then stable human-readable labels.
- **Output:** GROWTH, NORMAL, CAUTION or SUPPORT plus cluster characteristics.
- **Useful:** captures longer-term patterns beyond one month.
- **Safe:** the label supports explanation and personalization; it does not determine credit eligibility.

## 5. Recommendation engine

- **Input:** verified metrics, financial state, stress, segment and fictional catalog.
- **Processing:** auditable customer-first suitability rules.
- **Output:** prioritized guidance, “Why this?”, “Why NOT this?” and safer alternatives.
- **Useful:** turns analysis into an appropriate next action.
- **Safe:** stressed customers are not aggressively offered debt; catalog products are fictional.

## 6. Anomaly detection

- **Input:** the customer’s historical and recent transaction patterns.
- **Processing:** relative amount, merchant novelty, monthly spike, frequency, category shift and EMI-gap checks.
- **Output:** severity, confidence, detected signals and recommended review action.
- **Useful:** highlights activity worth checking early.
- **Safe:** the result is an anomaly indicator, never proof of fraud.

## 7. Loan impact simulation

- **Input:** proposed amount, rate, tenure and authenticated financial snapshot.
- **Processing:** standard EMI calculation and projected surplus, burden, buffer and stress.
- **Output:** current-versus-projected position, impact level, reasons and alternatives.
- **Useful:** makes affordability consequences visible before a commitment.
- **Safe:** described as financial suitability guidance, not approval or rejection.

## 8. NLP and local LLM

- **Input:** the customer question, language, limited conversation context and verified facts.
- **Processing:** local Ollama with `qwen3:1.7b`, concise generation and language-specific instructions.
- **Output:** conversational English, Hindi, Gujarati, Hinglish or Gujlish explanation.
- **Useful:** makes technical financial results accessible in the customer’s language.
- **Safe:** no external AI API; malformed or ungrounded output is rejected in favor of deterministic wording.

## 9. Grounded AI architecture

Known-domain questions first call the appropriate financial engine. Qwen may explain or rephrase the compact context but cannot create balances, scores, recommendations, anomaly facts, loan values or KYC decisions. Open-ended non-financial questions may use local Qwen directly.

## 10. Explainability

Every major result retains its source engine and evidence. UI “Why?” sections display deterministic explanations rather than asking the LLM to reverse-engineer a decision.
