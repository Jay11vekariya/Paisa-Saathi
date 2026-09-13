"""Deterministic proactive interventions built from verified financial engines."""
from datetime import datetime, timezone
import hashlib

from db import get_collection
from services.anomaly_detection import detect_anomalies
from services.customer_data import dashboard_for_authenticated, ledger_for_authenticated


SEVERITY_ORDER = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}


def _id(customer_id, alert_type, evidence_key):
    digest = hashlib.sha256(f'{customer_id}:{alert_type}:{evidence_key}'.encode()).hexdigest()[:12].upper()
    return f'PA-{digest}'


def _alert(customer_id, alert_type, severity, title, message, why, evidence,
           action, source, evidence_key, safer=None):
    return {
        'alert_id': _id(customer_id, alert_type, evidence_key), 'customer_id': customer_id,
        'type': alert_type, 'severity': severity, 'title': title, 'message': message,
        'why_it_matters': why, 'evidence': evidence, 'recommended_action': action,
        'safer_alternative': safer, 'created_at': datetime.now(timezone.utc).isoformat(),
        'status': 'UNREAD', 'source_engine': source,
    }


def _financial_alerts(analysis):
    cid, metrics = analysis['customer']['customer_id'], analysis['metrics']
    stress = analysis['financial_stress']
    state = analysis['financial_state']['state']
    period = analysis['period']['month']
    alerts = []
    if stress.get('status') == 'available' and stress.get('stress_level') in {'HIGH', 'CRITICAL'}:
        alerts.append(_alert(cid, 'FINANCIAL_STRESS', stress['stress_level'],
            'Saathi noticed cash-flow pressure',
            'Your recent verified pattern shows that financial flexibility is under pressure.',
            'Early support can protect essential spending and reduce the chance of taking on unaffordable debt.',
            [f"Stress score {stress['stress_score']}/100", f"Monthly surplus ₹{metrics['monthly_savings']:,.0f}",
             f"EMI burden {metrics['emi_burden']:.1f}%",
             f"Expense burden {(metrics['monthly_expenses'] / metrics['monthly_income'] * 100 if metrics['monthly_income'] else 0):.1f}%"],
            'Review an essentials-first budget and upcoming EMI obligations, then talk to Saathi.',
            'financial_stress', period,
            'Pause new borrowing; reduce discretionary spending or build a small repayment buffer first.'))
    if metrics['monthly_savings'] <= 0:
        alerts.append(_alert(cid, 'LOW_SURPLUS', 'HIGH', 'Monthly outgoings need attention',
            'Recorded outgoings currently meet or exceed income.',
            'A negative monthly surplus leaves less room for emergencies and repayments.',
            [f"Monthly income ₹{metrics['monthly_income']:,.0f}",
             f"Monthly outgoings ₹{metrics['monthly_expenses']:,.0f}",
             f"Monthly surplus ₹{metrics['monthly_savings']:,.0f}"],
            'Protect essentials first and review the largest discretionary categories.',
            'financial_health', period, 'Pause new borrowing while cash flow is negative.'))
    if metrics['emi_burden'] >= 35:
        alerts.append(_alert(cid, 'EMI_PRESSURE', 'HIGH' if metrics['emi_burden'] < 50 else 'CRITICAL',
            'EMI commitments are taking a large share',
            f"Scheduled EMI uses {metrics['emi_burden']:.1f}% of current income.",
            'Higher fixed obligations reduce monthly flexibility when income or expenses change.',
            [f"Scheduled EMI ₹{metrics['monthly_emi']:,.0f}", f"EMI burden {metrics['emi_burden']:.1f}%"],
            'Review upcoming EMI dates and avoid adding a new commitment without simulation.',
            'financial_health', period, 'Use the Loan Journey to compare a lower amount or wait for obligations to reduce.'))
    if metrics.get('savings_change_pct') is not None and metrics['savings_change_pct'] <= -15:
        alerts.append(_alert(cid, 'SAVINGS_DECLINE', 'MEDIUM', 'Savings declined recently',
            f"Net savings changed by {metrics['savings_change_pct']:.1f}% versus the previous completed month.",
            'A sustained decline can weaken the emergency buffer.',
            [f"Savings change {metrics['savings_change_pct']:.1f}%", f"Current surplus ₹{metrics['monthly_savings']:,.0f}"],
            'Review the categories that changed most before the next pay cycle.', 'financial_health', period))
    if state == 'GROWTH' and metrics['monthly_savings'] > 0:
        alerts.append(_alert(cid, 'POSITIVE_FINANCIAL_MOMENT', 'LOW', 'Your monthly position is resilient',
            'Your verified monthly cash flow remains positive.',
            'A positive surplus creates room to strengthen goals without increasing debt.',
            [f"Monthly surplus ₹{metrics['monthly_savings']:,.0f}", f"Savings rate {metrics['savings_rate']:.1f}%"],
            'Consider moving part of the surplus toward your stated goal or emergency buffer.',
            'financial_health', period))
    return alerts


def _anomaly_alerts(cid):
    customer, transactions, profile = ledger_for_authenticated(cid)
    result = detect_anomalies(customer, transactions, profile)
    alerts = []
    for item in result.get('recent_anomalies', []):
        alert_type = 'SPENDING_SPIKE' if item['anomaly_type'] == 'SPENDING_SPIKE' else (
            'FRAUD_RISK' if item['severity'] in {'HIGH', 'CRITICAL'} and item.get('transaction_id') else
            'UNUSUAL_TRANSACTION')
        alerts.append(_alert(cid, alert_type, item['severity'], item['title'], item['explanation'],
            'This differs from the customer’s own historical pattern and deserves review; it is not proof of fraud.',
            item['detected_signals'], item['recommended_action'], 'anomaly_detection', item['anomaly_id'],
            'If you recognise it, mark “This was me”; otherwise report it as suspicious in this prototype.'))
    return alerts


def _demo_fraud_alert(cid):
    return _alert(cid, 'FRAUD_RISK', 'CRITICAL', 'Saathi noticed an unusual transaction',
        'DEMO DATA: ₹52,000 at 3:15 AM from a new merchant in a different location.',
        'Several unusual signals occurred together. This is a review signal, not proof of fraud.',
        ['Amount ₹52,000 is unusual for this profile', 'Time 3:15 AM',
         'New merchant: Nova Digital', 'Location differs from the usual pattern'],
        'Confirm whether you recognise this synthetic transaction.', 'demo_scenario_fixture', 'aman-fraud',
        'Use “This was me” or “Report suspicious”; no real banking action is performed.')


def alerts_for_customer(cid, demo_scenario=None):
    alerts = _financial_alerts(dashboard_for_authenticated(cid)) + _anomaly_alerts(cid)
    if cid == 'PS004' and demo_scenario == 'fraud':
        alerts.insert(0, _demo_fraud_alert(cid))
    states = {row['alert_id']: row for row in get_collection('alerts').find(
        {'customer_id': cid}, {'_id': 0, 'alert_id': 1, 'status': 1})}
    for alert in alerts:
        alert['status'] = states.get(alert['alert_id'], {}).get('status', 'UNREAD')
    alerts.sort(key=lambda item: (item['status'] == 'DISMISSED', -SEVERITY_ORDER[item['severity']], item['alert_id']))
    return {'customer_id': cid, 'alerts': alerts,
            'unread_count': sum(item['status'] == 'UNREAD' for item in alerts),
            'methodology': 'Generated from verified financial and anomaly engines; alerts are guidance, not proof or lending decisions.'}


def update_alert(cid, alert_id, action, demo_scenario=None):
    current = alerts_for_customer(cid, demo_scenario)
    if alert_id not in {item['alert_id'] for item in current['alerts']}:
        return None
    statuses = {'read': 'READ', 'dismiss': 'DISMISSED', 'mine': 'CONFIRMED_BY_CUSTOMER',
                'report': 'REPORTED_SUSPICIOUS'}
    status = statuses[action]
    event = {'action': action, 'status': status, 'at': datetime.now(timezone.utc)}
    get_collection('alerts').update_one({'customer_id': cid, 'alert_id': alert_id}, {
        '$set': {'customer_id': cid, 'alert_id': alert_id, 'status': status, 'updated_at': event['at']},
        '$push': {'audit': event}}, upsert=True)
    return {'alert_id': alert_id, 'status': status, 'prototype_action': action in {'mine', 'report'}}
