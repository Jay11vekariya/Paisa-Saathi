"""Explainable anomaly indicators derived only from a customer's own ledger."""
from collections import Counter, defaultdict
from datetime import date
import hashlib
import statistics


MINIMUM_TRANSACTIONS = 20
MINIMUM_MONTHS = 3


def _identifier(customer_id, anomaly_type, transaction_id):
    raw = f'{customer_id}:{anomaly_type}:{transaction_id or "none"}'
    return f'AN-{hashlib.sha256(raw.encode()).hexdigest()[:12].upper()}'


def _alert(customer_id, anomaly_type, title, explanation, confidence, transaction,
           recommended_action, signals, severity='MEDIUM'):
    transaction = transaction or {}
    transaction_id = transaction.get('transaction_id')
    return {
        'anomaly_id': _identifier(customer_id, anomaly_type, transaction_id),
        'transaction_id': transaction_id,
        'severity': severity,
        'anomaly_type': anomaly_type,
        'title': title,
        'explanation': explanation,
        'confidence': round(max(0, min(1, confidence)), 2),
        'amount': round(float(transaction.get('amount', 0)), 2) if transaction else None,
        'merchant': transaction.get('merchant') if transaction else None,
        'date': transaction.get('date') if transaction else None,
        'recommended_action': recommended_action,
        'detected_signals': signals,
    }


def _month_key(row):
    return str(row.get('date', ''))[:7]


def detect_anomalies(customer, transactions, profile):
    customer_id = customer['customer_id']
    rows = sorted(transactions, key=lambda row: (row['date'], row['transaction_id']))
    months = sorted({_month_key(row) for row in rows if _month_key(row)})
    explanation = ('Indicators compare recent activity with this customer’s own historical pattern. '
                   'They are signals to review, not proof of fraud or wrongdoing.')
    if len(rows) < MINIMUM_TRANSACTIONS or len(months) < MINIMUM_MONTHS:
        return {
            'customer_id': customer_id, 'status': 'insufficient_data', 'total_anomalies': 0,
            'summary': {'total_alerts': 0, 'high_risk_alerts': 0, 'spending_behaviour': 'Not enough history'},
            'severity_counts': {level: 0 for level in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')},
            'recent_anomalies': [], 'explanation': explanation,
            'missing_information': ['At least 20 transactions', 'At least 3 months of transaction history'],
        }

    latest_month = months[-1]
    historical_months = months[:-1]
    debits = [row for row in rows if row['type'] == 'debit']
    recent = [row for row in debits if _month_key(row) == latest_month]
    historical = [row for row in debits if _month_key(row) in historical_months]
    alerts = []
    amounts = [float(row['amount']) for row in historical]
    mean = statistics.mean(amounts) if amounts else 0
    merchant_counts = Counter(str(row.get('merchant') or '').strip().lower() for row in historical)

    for row in recent:
        amount = float(row['amount'])
        merchant = str(row.get('merchant') or '').strip().lower()
        comparable = [float(item['amount']) for item in historical
                      if str(item.get('merchant') or '').strip().lower() == merchant]
        if len(comparable) < 3:
            comparable = [float(item['amount']) for item in historical if item.get('category') == row.get('category')]
        if len(comparable) < 3:
            comparable = amounts
        typical = statistics.mean(comparable) if comparable else mean
        typical_deviation = statistics.pstdev(comparable) if len(comparable) > 1 else 0
        threshold = typical + 3 * typical_deviation
        if typical and amount > max(threshold, typical * 2.5):
            ratio = amount / typical
            alerts.append(_alert(customer_id, 'UNUSUALLY_LARGE_TRANSACTION', 'Unusual activity detected',
                f"₹{amount:,.0f} is {ratio:.1f}× the typical ₹{typical:,.0f} for comparable past payments.",
                min(.98, .64 + (ratio - 2.5) * .08), row,
                'Confirm that you recognise the transaction and contact your provider if you do not.',
                [f'Amount is {ratio:.1f}× comparable historical payments', 'Compared with the same merchant or category'],
                'HIGH' if ratio < 5 else 'CRITICAL'))
        if amount >= max(mean * 1.5, 2000) and merchant_counts[merchant] <= 1:
            alerts.append(_alert(customer_id, 'UNUSUAL_MERCHANT', 'New or unusual merchant',
                'This significant payment is to a merchant that rarely appears in your earlier history.',
                .72 if merchant_counts[merchant] == 0 else .62, row,
                'Check the merchant name and payment details before taking any further action.',
                ['Merchant appeared once or less historically', f'Amount ₹{amount:,.0f} is significant for this ledger'],
                'MEDIUM'))

    totals = defaultdict(float)
    counts = Counter()
    for row in debits:
        totals[_month_key(row)] += float(row['amount'])
        counts[_month_key(row)] += 1
    previous_totals = [totals[month] for month in historical_months]
    normal_total = statistics.mean(previous_totals) if previous_totals else 0
    latest_total = totals[latest_month]
    representative = max(recent, key=lambda row: row['amount'], default=None)
    if normal_total and latest_total > normal_total * 1.25:
        ratio = latest_total / normal_total
        alerts.append(_alert(customer_id, 'SPENDING_SPIKE', 'Recent spending spike',
            f"Spending in {latest_month} is {(ratio - 1) * 100:.0f}% above your earlier monthly average.",
            min(.95, .65 + (ratio - 1.25)), representative,
            'Review this month’s largest expenses and confirm that the increase was expected.',
            [f'Recent spending ₹{latest_total:,.0f}', f'Historical monthly average ₹{normal_total:,.0f}'],
            'HIGH' if ratio >= 1.5 else 'MEDIUM'))

    normal_count = statistics.mean([counts[month] for month in historical_months]) if historical_months else 0
    if normal_count and counts[latest_month] >= max(normal_count * 1.5, normal_count + 8):
        alerts.append(_alert(customer_id, 'UNUSUAL_FREQUENCY', 'Unusual transaction frequency',
            f"{counts[latest_month]} debits were recorded this month versus a normal level near {normal_count:.0f}.",
            .7, representative, 'Review the recent transaction list for duplicates or unfamiliar payments.',
            [f'{counts[latest_month]} recent debits', f'{normal_count:.0f} average monthly debits'], 'MEDIUM'))

    historical_categories, recent_categories = defaultdict(float), defaultdict(float)
    for row in historical: historical_categories[row.get('category')] += float(row['amount'])
    for row in recent: recent_categories[row.get('category')] += float(row['amount'])
    historical_total = sum(historical_categories.values())
    recent_total = sum(recent_categories.values())
    shifts = []
    if historical_total and recent_total:
        for category in set(historical_categories) | set(recent_categories):
            old_share = historical_categories[category] / historical_total
            new_share = recent_categories[category] / recent_total
            shifts.append((new_share - old_share, category, old_share, new_share))
    if shifts and max(shifts)[0] >= .2:
        change, category, old_share, new_share = max(shifts)
        anchor = max((row for row in recent if row.get('category') == category),
                     key=lambda row: row['amount'], default=representative)
        alerts.append(_alert(customer_id, 'SUDDEN_BEHAVIOUR_CHANGE', 'Spending behaviour changed',
            f"{category} moved from {old_share * 100:.0f}% to {new_share * 100:.0f}% of debit spending this month.",
            min(.9, .6 + change), anchor, 'Review the changed category and confirm that the new pattern was expected.',
            [f'{category} share increased by {change * 100:.0f} percentage points', 'Compared with all earlier months'],
            'HIGH' if change >= .35 else 'MEDIUM'))

    expected_emi = float(customer.get('monthly_emi') or 0)
    recent_emi = sum(float(row['amount']) for row in recent if row.get('category') == 'EMI')
    if expected_emi > 0 and recent_emi < expected_emi * .9:
        prior_emi = next((row for row in reversed(historical) if row.get('category') == 'EMI'), None)
        alerts.append(_alert(customer_id, 'EMI_PAYMENT_GAP', 'Scheduled payment needs review',
            f"Recorded EMI payments for {latest_month} are below the expected ₹{expected_emi:,.0f}. This may be a recording gap and is not proof of a missed payment.",
            .9, prior_emi, 'Check the scheduled payment and your latest account statement.',
            [f'Recorded EMI ₹{recent_emi:,.0f}', f'Expected EMI ₹{expected_emi:,.0f}'], 'HIGH'))

    alerts.sort(key=lambda item: ({'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}[item['severity']], item['date'] or ''), reverse=True)
    counts_by_severity = {level: sum(item['severity'] == level for item in alerts) for level in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')}
    high_risk = counts_by_severity['HIGH'] + counts_by_severity['CRITICAL']
    behaviour = 'Needs review' if high_risk else 'Changed recently' if alerts else 'Within usual pattern'
    return {
        'customer_id': customer_id, 'status': 'available', 'total_anomalies': len(alerts),
        'summary': {'total_alerts': len(alerts), 'high_risk_alerts': high_risk, 'spending_behaviour': behaviour},
        'severity_counts': counts_by_severity, 'recent_anomalies': alerts[:10],
        'explanation': explanation,
    }
