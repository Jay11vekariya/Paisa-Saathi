"""Transparent financial-stress indicator built from calculated cash-flow metrics.

This is a prototype wellness signal. It is not a credit score, lending decision,
or statement of loan eligibility.
"""
import math


LEVELS = ((25, 'LOW'), (50, 'MODERATE'), (75, 'HIGH'), (101, 'CRITICAL'))
MINIMUM_OBSERVED_MONTHS = 2
MINIMUM_TRANSACTIONS = 6


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def _factor(key, name, weight, stress, value, explanation, positive_explanation=None):
    points = round(_clamp(stress) * weight / 100, 1)
    impact = 'positive' if stress <= 30 else 'negative' if stress >= 60 else 'neutral'
    return {
        'key': key,
        'name': name,
        'weight': weight,
        'points': points,
        'impact': impact,
        'value': value,
        'explanation': positive_explanation if impact == 'positive' and positive_explanation else explanation,
    }


def _guidance(level):
    return {
        'LOW': [
            'Keep a consistent savings habit.',
            'Build or maintain an accessible emergency fund.',
            'Plan longer-term goals without stretching monthly cash flow.',
        ],
        'MODERATE': [
            'Review discretionary spending and set a practical monthly budget.',
            'Increase the emergency buffer gradually.',
            'Check that recurring commitments still fit comfortably.',
        ],
        'HIGH': [
            'Stabilise monthly cash flow before taking on new debt.',
            'Review existing commitments and prioritise essential payments.',
            'Create a realistic budget or repayment plan.',
        ],
        'CRITICAL': [
            'Use a support-first budget focused on essentials.',
            'Avoid unnecessary new borrowing while cash flow is under pressure.',
            'Review repayment or support options for existing commitments.',
        ],
    }[level]


def insufficient_stress(customer_id, data_quality):
    return {
        'customer_id': customer_id,
        'status': 'insufficient_data',
        'stress_score': None,
        'stress_level': None,
        'factors': [],
        'positive_factors': [],
        'guidance': ['We need more transaction history to estimate your financial stress.'],
        'data_quality': data_quality,
        'methodology': (
            f'At least {MINIMUM_OBSERVED_MONTHS} observed months and {MINIMUM_TRANSACTIONS} '
            'transactions are required. No financial behaviour is invented.'
        ),
    }


def calculate_stress(customer_id, metrics, data_quality):
    """Calculate a 0-100 stress score; higher means more estimated stress."""
    if (data_quality.get('observed_months', 0) < MINIMUM_OBSERVED_MONTHS or
            data_quality.get('transaction_count', 0) < MINIMUM_TRANSACTIONS):
        return insufficient_stress(customer_id, data_quality)

    income = metrics['monthly_income']
    expenses = metrics['monthly_expenses']
    expense_ratio = expenses / income * 100 if income > 0 else (100 if expenses else 0)
    income_stress = 100 if metrics['income_disruption'] else 100 - metrics['income_stability']
    expense_burden_stress = _clamp((expense_ratio - 50) / 50 * 100)
    savings_stress = _clamp((25 - metrics['savings_rate']) / 35 * 100)
    if metrics['savings_change_pct'] is not None and metrics['savings_change_pct'] < 0:
        savings_stress = max(savings_stress, _clamp(abs(metrics['savings_change_pct']) * 2))
    debt_stress = _clamp(metrics['emi_burden'] / 50 * 100)
    if metrics['emi_payment_gap']:
        debt_stress = 100
    surplus_stress = _clamp((20 - metrics['savings_rate']) / 30 * 100)
    trend_stress = max(100 - metrics['expense_stability'], _clamp((metrics['expense_change_pct'] or 0) * 4))
    buffer_stress = _clamp((6 - metrics['emergency_buffer_months']) / 6 * 100)

    factors = [
        _factor('income_stability', 'Income stability', 20, income_stress,
                'Disrupted' if metrics['income_disruption'] else f"{metrics['income_stability']:.1f}% stable",
                'Income has become less stable or has fallen materially.', 'Income remains relatively consistent.'),
        _factor('expense_burden', 'Expense burden', 20, expense_burden_stress, f'{expense_ratio:.1f}% of income',
                'Monthly outgoings consume a large share of recorded income.', 'Monthly outgoings leave comfortable room in recorded income.'),
        _factor('savings_behaviour', 'Savings behaviour', 15, savings_stress, f"{metrics['savings_rate']:.1f}% retained",
                'The savings rate or recent savings direction needs attention.', 'The current savings rate supports financial resilience.'),
        _factor('debt_burden', 'Debt and EMI burden', 15, debt_stress, f"{metrics['emi_burden']:.1f}% of income",
                'Scheduled EMI burden or recorded payment coverage adds pressure.', 'Scheduled EMI remains manageable relative to income.'),
        _factor('cash_flow', 'Monthly cash-flow surplus', 15, surplus_stress, f"₹{metrics['monthly_savings']:,.0f}",
                'Little or no monthly surplus is available after outgoings.', 'A positive monthly surplus provides breathing room.'),
        _factor('spending_pattern', 'Spending pattern', 10, trend_stress,
                f"{metrics['expense_change_pct']:+.1f}% change" if metrics['expense_change_pct'] is not None else 'No comparable trend',
                'Spending is volatile or has risen sharply.', 'Spending remains relatively steady.'),
        _factor('emergency_buffer', 'Emergency buffer', 5, buffer_stress, f"{metrics['emergency_buffer_months']:.1f} months",
                'The accessible buffer may not cover several months of outgoings.', 'The accessible balance provides a useful emergency cushion.'),
    ]
    score = min(100, max(0, math.floor(sum(item['points'] for item in factors) + .5)))
    level = next(label for upper, label in LEVELS if score < upper)
    return {
        'customer_id': customer_id,
        'status': 'available',
        'stress_score': score,
        'stress_level': level,
        'factors': factors,
        'positive_factors': [item for item in factors if item['impact'] == 'positive'],
        'guidance': _guidance(level),
        'data_quality': data_quality,
        'methodology': (
            'Estimated financial stress uses income stability (20%), expense burden (20%), '
            'savings behaviour (15%), debt/EMI burden (15%), cash-flow surplus (15%), '
            'spending pattern (10%), and emergency buffer (5%). It is not a credit score '
            'or loan-eligibility assessment.'
        ),
    }
