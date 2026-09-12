"""Loan impact guidance using an authenticated customer's calculated finances."""
import math


def _money(value):
    return round(float(value), 2)


def calculate_emi(amount, annual_rate, months):
    monthly_rate = annual_rate / 1200
    if monthly_rate == 0:
        return amount / months
    growth = (1 + monthly_rate) ** months
    return amount * monthly_rate * growth / (growth - 1)


def simulate_loan(analysis, inputs):
    metrics = analysis['metrics']
    missing = [key for key in ('monthly_income', 'monthly_expenses', 'monthly_savings', 'account_balance')
               if metrics.get(key) is None]
    if missing:
        return {'customer_id': analysis['customer']['customer_id'], 'status': 'insufficient_data', 'missing_information': missing,
                'message': 'Complete the missing financial information before simulating a loan impact.'}
    amount, rate, months = inputs['loan_amount'], inputs['annual_interest_rate'], inputs['tenure_months']
    emi = calculate_emi(amount, rate, months)
    total_repayment = emi * months
    income = float(metrics['monthly_income'])
    expenses = float(metrics['monthly_expenses'])
    savings = float(metrics['monthly_savings'])
    current_emi = float(inputs.get('existing_emi') if inputs.get('existing_emi') is not None else metrics.get('monthly_emi') or 0)
    average_expenses = float(metrics.get('average_monthly_expenses') or expenses)
    balance = float(metrics['account_balance'])
    projected_surplus = savings - emi
    current_burden = current_emi / income * 100 if income else None
    projected_burden = (current_emi + emi) / income * 100 if income else None
    current_buffer = float(metrics.get('emergency_buffer_months') or 0)
    projected_buffer = max(0, balance) / (average_expenses + emi) if average_expenses + emi else 0
    projected_savings_rate = projected_surplus / income * 100 if income else None
    current_stress = analysis['financial_stress'].get('stress_score')
    stress_increase = min(35, (emi / income * 55 if income else 35) + (15 if projected_surplus <= 0 else 0))
    projected_stress = min(100, round((current_stress or 0) + stress_increase)) if current_stress is not None else None

    score = 0
    if projected_surplus <= 0: score += 50
    elif projected_savings_rate is not None and projected_savings_rate < 5: score += 32
    elif projected_savings_rate is not None and projected_savings_rate < 15: score += 18
    if projected_burden is None: score += 40
    elif projected_burden >= 65: score += 45
    elif projected_burden >= 45: score += 30
    elif projected_burden >= 30: score += 16
    if projected_buffer < 1: score += 22
    elif projected_buffer < 3: score += 10
    if analysis['financial_state']['state'] == 'SUPPORT': score += 18
    elif analysis['financial_state']['state'] == 'CAUTION': score += 10
    score = min(100, round(score))
    if projected_surplus <= 0 or (projected_burden is not None and projected_burden >= 65) or score >= 75:
        level = 'CRITICAL'
    elif (projected_burden is not None and projected_burden >= 45) or score >= 48:
        level = 'HIGH IMPACT'
    elif score >= 20 or (projected_burden is not None and projected_burden >= 30):
        level = 'CAUTION'
    else:
        level = 'SAFE'

    key_impacts = [
        f"Monthly surplus changes from ₹{savings:,.0f} to ₹{projected_surplus:,.0f}.",
        f"EMI burden changes from {current_burden:.1f}% to {projected_burden:.1f}% of income." if current_burden is not None else 'EMI burden cannot be estimated without monthly income.',
        f"Estimated emergency coverage changes from {current_buffer:.1f} to {projected_buffer:.1f} months.",
    ]
    risk_factors, positive_factors = [], []
    (risk_factors if projected_surplus <= 0 else positive_factors).append(
        'Projected monthly cash flow is negative.' if projected_surplus <= 0 else 'Projected monthly cash flow remains positive.')
    if projected_burden is not None and projected_burden >= 35: risk_factors.append('Combined EMI burden exceeds 35% of monthly income.')
    else: positive_factors.append('Combined EMI burden remains below 35% of monthly income.')
    if projected_buffer < 3: risk_factors.append('Estimated emergency coverage would be below three months.')
    else: positive_factors.append('Estimated emergency coverage remains at least three months.')
    alternatives = []
    if level != 'SAFE':
        alternatives.extend(['Reduce the loan amount.', 'Compare a longer tenure while checking the added total interest.'])
    if projected_buffer < 3: alternatives.append('Delay borrowing until emergency savings improve.')
    if projected_burden is not None and projected_burden >= 35: alternatives.append('Reduce other EMI commitments first.')
    recommendation = {
        'SAFE': 'The projected commitment appears manageable under the current recorded financial pattern.',
        'CAUTION': 'The loan may be manageable, but it would noticeably reduce monthly flexibility.',
        'HIGH IMPACT': 'The projected EMI would place substantial pressure on current cash flow.',
        'CRITICAL': 'The projected commitment would create severe cash-flow or debt-burden pressure.',
    }[level]
    snapshot = {
        'monthly_income': _money(income), 'monthly_expenses': _money(expenses),
        'monthly_surplus': _money(savings), 'emi': _money(current_emi),
        'emi_burden_pct': round(current_burden, 1) if current_burden is not None else None,
        'savings_capacity_pct': round(savings / income * 100, 1) if income else None,
        'emergency_buffer_months': round(current_buffer, 2),
        'financial_state': analysis['financial_state']['state'],
        'financial_stress_score': current_stress,
        'customer_segment': analysis['segmentation'].get('segment'),
    }
    projected = {
        **snapshot, 'monthly_expenses': _money(expenses + emi), 'monthly_surplus': _money(projected_surplus),
        'emi': _money(current_emi + emi),
        'emi_burden_pct': round(projected_burden, 1) if projected_burden is not None else None,
        'savings_capacity_pct': round(projected_savings_rate, 1) if projected_savings_rate is not None else None,
        'emergency_buffer_months': round(projected_buffer, 2), 'financial_stress_score': projected_stress,
    }
    return {
        'customer_id': analysis['customer']['customer_id'], 'status': 'available',
        'loan_inputs': inputs, 'emi': _money(emi),
        'total_interest': _money(total_repayment - amount), 'total_repayment': _money(total_repayment),
        'current_financial_snapshot': snapshot, 'projected_financial_snapshot': projected,
        'impact_level': level, 'impact_score': score, 'key_impacts': key_impacts,
        'risk_factors': risk_factors, 'positive_factors': positive_factors,
        'recommendation': recommendation,
        'safer_alternative': alternatives or ['Maintain the planned repayment buffer and review the scenario if income or expenses change.'],
        'disclaimer': 'Prototype financial guidance only. This is not a loan approval or eligibility decision.',
    }
