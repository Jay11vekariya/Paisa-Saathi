"""Deterministic, explainable recommendations for synthetic customer data.

This pure decision layer accepts verified calculated metrics, state, and the
fictional catalog. That separation keeps it auditable and leaves a future seam
for model-ranked candidates without replacing customer-safety rules.
"""


def _product(products, product_id):
    return next((item for item in products if item['product_id'] == product_id), None)


def _conditions(metrics, state, stress=None, segmentation=None):
    """Return only customer conditions that are actually present."""
    conditions = []
    if metrics['income_disruption']:
        conditions.append('Latest recorded income is below 65% of the earlier monthly average.')
    if metrics['emi_payment_gap']:
        conditions.append('Recorded EMI payments are below 90% of the scheduled EMI amount.')
    if metrics['emi_burden'] > 35:
        conditions.append(f"Scheduled EMI uses {metrics['emi_burden']:.1f}% of current income.")
    if metrics['expense_change_pct'] is not None and metrics['expense_change_pct'] > 10 and metrics['savings_change_amount'] < 0:
        conditions.append('Expenses increased by more than 10% while savings fell.')
    if metrics['savings_rate'] < 0:
        conditions.append('Current outgoings exceed current income.')
    if metrics['emergency_buffer_months'] < 1:
        conditions.append(f"Emergency savings cover only {metrics['emergency_buffer_months']:.1f} months of average outgoings.")
    if stress and stress.get('status') == 'available' and stress['stress_level'] in {'HIGH', 'CRITICAL'}:
        conditions.append(f"Estimated financial stress is {stress['stress_level']} ({stress['stress_score']}/100).")
    if segmentation and segmentation.get('status') == 'available' and segmentation['segment'] in {'CAUTION', 'SUPPORT'}:
        conditions.append(f"Longer-term financial behaviour is in the {segmentation['segment']} segment.")
    return conditions or [f"Current calculated financial state is {state.lower()}."]


def _recommendation(product, action, reason, why_this, why_help, priority, suitability, confidence):
    return {'product': product, 'action': action, 'category': product['category'], 'reason': reason,
            'why_this': why_this, 'why_it_may_help': why_help, 'suitability': suitability,
            'confidence': confidence, 'priority': priority}


def _rejection(product, why_not, conditions, action, reason):
    return {'product': product, 'category': product['category'], 'why_not_this': why_not,
            'rejection_conditions': conditions,
            'safer_alternative': {'action': action, 'category': 'Financial guidance', 'reason': reason}}


def recommend(metrics, financial_state, products, stress=None, segmentation=None):
    """Return stable, customer-first recommendations from verified analysis.

    A catalog item is suggested only when a rule connects it to a calculated
    need. The rules never assess lending eligibility or suggest debt by default.
    """
    catalog = sorted(products, key=lambda item: item['product_id'])
    state, income = financial_state['state'], metrics['monthly_income']
    stress_level = stress.get('stress_level') if stress and stress.get('status') == 'available' else None
    segment = segmentation.get('segment') if segmentation and segmentation.get('status') == 'available' else None
    decision_state = state
    if stress_level == 'CRITICAL' or segment == 'SUPPORT':
        decision_state = 'SUPPORT'
    elif (stress_level == 'HIGH' or segment == 'CAUTION') and state in {'GROWTH', 'NORMAL'}:
        decision_state = 'CAUTION'
    buffer, savings_rate = metrics['emergency_buffer_months'], metrics['savings_rate']
    conditions = _conditions(metrics, state, stress, segmentation)
    recommendations, not_recommended = [], []

    def include(product_id, action, reason, why_this, why_help, priority, suitability, confidence):
        product = _product(catalog, product_id)
        if product:
            recommendations.append(_recommendation(product, action, reason, why_this, why_help, priority, suitability, confidence))

    def reject(product_id, why_not, action, reason, rejection_conditions=conditions):
        product = _product(catalog, product_id)
        if product:
            not_recommended.append(_rejection(product, why_not, rejection_conditions, action, reason))

    if decision_state == 'SUPPORT':
        include('PR007', 'Create an essentials-first monthly budget', 'Cash flow needs stabilising before new commitments.',
                'Recent income or recorded EMI payments need attention before new commitments.',
                'It focuses the next step on essential outgoings, payment review, and a workable monthly plan.', 'NOW', 'Strong fit', 'High')
        include('PR008', 'Set a small emergency-savings target', 'A safety buffer can reduce pressure from unexpected costs.',
                f'Your current emergency buffer is {buffer:.1f} months of average outgoings.',
                'A small, realistic buffer target can improve resilience once essential bills are covered.', 'NEXT', 'Good fit', 'High')
        reject('PR005', 'A new loan could add a fixed payment while cash flow is under pressure.',
               'Review essentials and create a repayment plan', 'Address scheduled payments and discretionary spending before taking on new debt.')
        reject('PR003', 'Investment risk is not a priority while income or scheduled payments need review.',
               'Build accessible emergency savings first', 'Keep money available for essentials before considering long-term investment risk.')
        reject('PR002', 'A fixed recurring contribution may be hard to sustain until cash flow stabilises.',
               'Use a flexible weekly savings target', 'Set aside only what remains after essential bills and scheduled payments.')
    elif decision_state == 'CAUTION':
        include('PR008', 'Build an accessible emergency buffer', 'Caution signals make accessible savings more valuable than extra commitments.',
                f'Your buffer is {buffer:.1f} months and your financial state has caution signals.',
                'Building accessible emergency savings can reduce the need to rely on new borrowing for surprises.', 'NOW', 'Strong fit', 'High')
        if metrics['emi_burden'] > 35 or metrics['emi_payment_gap']:
            include('PR006', 'Review repayment capacity and scheduled EMIs', 'Your debt commitments need review before adding any new credit.',
                    f"Scheduled EMI uses {metrics['emi_burden']:.1f}% of current income or needs a payment review.",
                    'It supports reviewing commitments and payment capacity without adding another credit product.', 'NOW', 'Strong fit', 'High')
        else:
            include('PR007', 'Tighten the monthly spending plan', 'Savings or spending signals need a closer monthly plan.',
                    'Your calculated caution state shows that spending and savings need attention.',
                    'A practical cash-flow review can help protect essentials and create room for savings.', 'NEXT', 'Good fit', 'High')
        reject('PR005', 'Current caution signals make adding a new fixed repayment unsuitable right now.',
               'Reduce discretionary spending and review repayments', 'Create breathing room in the monthly plan before considering any new debt.')
        reject('PR003', 'Strengthening cash flow and the emergency buffer comes before taking investment risk.',
               'Grow accessible emergency savings', 'Prioritise liquid savings until the caution signals improve.')
    elif decision_state == 'GROWTH':
        if savings_rate >= 20 and income >= 15000:
            include('PR002', 'Automate a goal-based monthly saving amount', 'Stable positive savings can support a regular goal contribution.',
                    f'You retained {savings_rate:.1f}% of income and your cash flow is currently stable.',
                    'A regular savings habit may help you work toward a chosen goal while keeping contributions within your plan.', 'NEXT', 'Strong fit', 'High')
        if buffer >= 6 and income >= 30000:
            include('PR003', 'Learn about diversified long-term investing', 'Your strong buffer makes learning about longer-term choices more appropriate.',
                    f'Your buffer covers {buffer:.1f} months of average outgoings and savings are positive.',
                    'Its learning-focused approach can help you understand diversified investing; returns are not promised.', 'CONSIDER', 'Potential fit', 'Medium')
        else:
            include('PR008', 'Keep building emergency savings toward six months', 'A larger buffer improves flexibility before long-term risk-taking.',
                    f'Your buffer is {buffer:.1f} months, below the six-month resilience benchmark used here.',
                    'Increasing accessible savings first can make later long-term choices more comfortable.', 'NEXT', 'Good fit', 'High')
        if income >= 20000:
            include('PR004', 'Review basic health-cost protection needs', 'Stable finances make it reasonable to understand protection options.',
                    'Your income and current financial state support reviewing basic protection needs.',
                    'Understanding health-cover options can help plan for unexpected health costs; this prototype has no policy terms.', 'CONSIDER', 'Potential fit', 'Medium')
        reject('PR005', 'There is no stated borrowing need in the available financial data, so a loan is not recommended.',
               'Keep savings aligned to a chosen goal', 'Use the current positive cash flow to strengthen savings before considering debt.')
    else:  # NORMAL
        if buffer < 3:
            include('PR008', 'Build a three-month emergency-savings target', 'Your buffer can be strengthened before adding more complex commitments.',
                    f'Your emergency buffer is {buffer:.1f} months of average outgoings.',
                    'A clearer emergency-savings target can make routine finances more resilient.', 'NEXT', 'Strong fit', 'High')
        include('PR001', 'Keep emergency savings separate and accessible', 'Accessible savings are a useful foundation for a manageable financial position.',
                'Your finances are manageable, so keeping savings accessible is a useful foundation.',
                'An accessible savings option can separate a planned buffer from everyday spending.', 'NEXT', 'Good fit', 'High')
        if income >= 20000:
            include('PR004', 'Review basic health-cost protection needs', 'Steady cash flow allows time to understand basic protection needs.',
                    'Your cash flow is currently steady enough to review basic protection needs.',
                    'Learning about health-cover options can help with planning; this prototype has no policy terms.', 'CONSIDER', 'Potential fit', 'Medium')
        reject('PR005', 'There is no stated borrowing goal, so adding a loan is not customer-beneficial by default.',
               'Maintain savings and review the monthly plan', 'Use available cash flow for known priorities instead of adding debt without a clear need.')
        if buffer < 3:
            reject('PR003', 'Build a stronger accessible emergency buffer before taking investment risk.',
                   'Complete the emergency-savings target', 'Keep the buffer available for surprises before considering long-term investment choices.')

    priority_order = {'NOW': 0, 'NEXT': 1, 'CONSIDER': 2}
    recommendations.sort(key=lambda item: (priority_order[item['priority']], item['product']['product_id']))
    not_recommended.sort(key=lambda item: item['product']['product_id'])
    recommended_focus = financial_state['recommended_focus']
    if decision_state != state and stress and stress.get('guidance'):
        recommended_focus = stress['guidance'][0]
    return {'financial_state': state, 'decision_state': decision_state,
            'financial_stress': stress, 'segmentation': segmentation,
            'recommended_focus': recommended_focus,
            'engine': {'version': 'rules-v1', 'decision_mode': 'deterministic',
                       'signals_used': ['financial_state', 'financial_stress', 'customer_segment', 'monthly_income', 'savings_rate', 'emi_burden', 'emergency_buffer_months']},
            'recommendations': recommendations, 'not_recommended': not_recommended,
            'methodology': 'Deterministic rules use the calculated financial state, estimated stress, K-Means segment, cash flow, EMI burden, and emergency buffer. This is prototype guidance, not a credit or eligibility decision.'}
