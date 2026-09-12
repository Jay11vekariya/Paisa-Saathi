"""Explainable rule-based wellness states; never a lending decision."""
def determine_state(metrics):
    m = metrics
    support = []
    if m['income_disruption']:
        support.append('Latest income is below 65% of the preceding monthly average.')
    if m['emi_payment_gap']:
        support.append('Recorded EMI payments are below 90% of the expected EMI; this is an indicator to review, not proof of a missed payment.')
    if m['savings_rate'] < -20 or m['account_balance'] < 0:
        support.append('Outgoings materially exceed income or the reconstructed balance is negative.')
    if support:
        return result('SUPPORT','Support Mode','Your recent cash flow needs some breathing room.',support,'Review essential outgoings and scheduled payments first.')
    caution = []
    if m['emi_burden'] > 35:
        caution.append('Expected monthly EMI exceeds 35% of current income.')
    if m['expense_change_pct'] is not None and m['expense_change_pct'] > 10 and m['savings_change_amount'] < 0:
        caution.append('Expenses rose by more than 10% while savings fell.')
    if m['savings_rate'] < 5:
        caution.append('Less than 5% of current income remains after outgoings.')
    if caution:
        return result('CAUTION','Caution Mode','A few spending and debt signals deserve a closer look.',caution,'Stabilise spending and preserve an emergency buffer.')
    if m['income_stability'] >= 85 and m['savings_change_amount'] > 0 and m['savings_rate'] >= 20 and m['emi_burden'] <= 30 and m['emergency_buffer_months'] >= 3:
        return result('GROWTH','Growth Mode','Your savings are moving forward, with steady income and manageable debt.',
                      ['Savings increased compared with the previous month.','Income is stable and EMI stays within 30% of income.','Your balance covers at least three average months of outgoings.'],
                      'Build savings and long-term financial resilience.')
    return result('NORMAL','Normal Mode','Your finances are following a steady, manageable rhythm.',
                  ['No support or caution thresholds were triggered.','Keep tracking savings, regular expenses and your emergency buffer.'],
                  'Maintain consistent savings and review your monthly plan.')

def result(state,title,description,reasons,focus):
    return dict(state=state,title=title,description=description,reasons=reasons,recommended_focus=focus)

def insight_for(state, metrics):
    if state['state'] == 'GROWTH':
        return f"Your savings rose by ₹{metrics['savings_change_amount']:,.0f} over the previous month. Keep this rhythm to strengthen your {metrics['emergency_buffer_months']:.1f}-month emergency buffer."
    if state['state'] == 'SUPPORT':
        return 'Your recent income or payment pattern has changed. Start by reviewing essential expenses and recorded EMI payments before adding new commitments.'
    if state['state'] == 'CAUTION':
        return f"Scheduled EMI represents {metrics['emi_burden']:.1f}% of this month’s income. Reviewing flexible spending could create more room in your monthly plan."
    return f"You retained {metrics['savings_rate']:.1f}% of this month’s income after outgoings. A consistent savings habit can help your buffer grow over time."
