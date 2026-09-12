"""Reproducible K-Means customer segmentation over verified analytics."""
from hashlib import sha256
import json
from threading import RLock

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


FEATURES = (
    'monthly_income', 'average_monthly_expenses', 'monthly_savings', 'savings_rate',
    'emi_burden', 'income_stability', 'expense_stability', 'emergency_buffer_months',
    'expense_change_pct', 'transactions_per_month', 'stress_score',
)
SEGMENTS = ('GROWTH', 'BALANCED', 'CAUTION', 'SUPPORT')
DESCRIPTIONS = {
    'GROWTH': 'Your longer-term pattern shows stronger savings, surplus, and financial resilience.',
    'BALANCED': 'Your longer-term income and spending patterns are broadly manageable.',
    'CAUTION': 'Your longer-term pattern shows tighter cash flow or rising financial pressure.',
    'SUPPORT': 'Your longer-term pattern suggests that stabilising cash flow should come first.',
}
_MODEL_CACHE = {}
_MODEL_LOCK = RLock()


def feature_vector(analysis):
    metrics = analysis['metrics']
    stress = analysis['financial_stress']
    quality = analysis['data_quality']
    if stress['status'] != 'available':
        return None
    months = max(quality['observed_months'], 1)
    return [
        float(metrics['monthly_income']), float(metrics['average_monthly_expenses']),
        float(metrics['monthly_savings']), float(metrics['savings_rate']),
        float(metrics['emi_burden']), float(metrics['income_stability']),
        float(metrics['expense_stability']), float(metrics['emergency_buffer_months']),
        float(metrics['expense_change_pct'] or 0), float(quality['transaction_count']) / months,
        float(stress['stress_score']),
    ]


def _bundle(analyses, clusters=4):
    rows = [feature_vector(item) for item in analyses]
    rows = [row for row in rows if row is not None and all(np.isfinite(row))]
    if len(rows) < clusters or len({tuple(row) for row in rows}) < clusters:
        return None
    signature = sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    with _MODEL_LOCK:
        if signature in _MODEL_CACHE:
            return _MODEL_CACHE[signature]
        scaler = StandardScaler()
        scaled = scaler.fit_transform(rows)
        model = KMeans(n_clusters=clusters, random_state=42, n_init=20).fit(scaled)
        centroids = scaler.inverse_transform(model.cluster_centers_)
        stress_index = FEATURES.index('stress_score')
        savings_index = FEATURES.index('savings_rate')
        # Rank centroid risk, with stress dominant and savings as a deterministic tie-breaker.
        ordered = sorted(range(clusters), key=lambda cluster: (centroids[cluster][stress_index], -centroids[cluster][savings_index]))
        label_by_cluster = {cluster: SEGMENTS[index] for index, cluster in enumerate(ordered)}
        result = {'scaler': scaler, 'model': model, 'centroids': centroids, 'labels': label_by_cluster}
        _MODEL_CACHE.clear()
        _MODEL_CACHE[signature] = result
        return result


def _characteristics(analysis):
    metrics = analysis['metrics']
    stress = analysis['financial_stress']
    rows = []
    rows.append(('positive' if metrics['income_stability'] >= 80 and not metrics['income_disruption'] else 'negative',
                 'Income is relatively stable' if metrics['income_stability'] >= 80 and not metrics['income_disruption'] else 'Income stability needs attention'))
    rows.append(('positive' if metrics['savings_rate'] >= 15 else 'negative',
                 f"{metrics['savings_rate']:.1f}% of income is retained" if metrics['savings_rate'] >= 15 else 'Savings leave limited monthly room'))
    rows.append(('positive' if metrics['emi_burden'] <= 30 and not metrics['emi_payment_gap'] else 'negative',
                 'Debt burden is manageable' if metrics['emi_burden'] <= 30 and not metrics['emi_payment_gap'] else 'Debt or recorded EMI payments need review'))
    rows.append(('positive' if stress['stress_level'] in {'LOW', 'MODERATE'} else 'negative',
                 f"Estimated financial stress is {stress['stress_level']}"))
    return [{'impact': impact, 'text': text} for impact, text in rows]


def insufficient_segment(customer_id, data_quality):
    return {
        'customer_id': customer_id,
        'status': 'insufficient_data',
        'segment': None,
        'segment_description': 'We need more transaction history to estimate your financial behaviour.',
        'confidence': None,
        'key_characteristics': [],
        'data_quality': data_quality,
        'model': {'algorithm': 'K-Means', 'clusters': 4, 'features': list(FEATURES), 'trained': False},
    }


def segment_customer(analysis, training_analyses):
    customer_id = analysis['customer']['customer_id']
    vector = feature_vector(analysis)
    if vector is None:
        return insufficient_segment(customer_id, analysis['data_quality'])
    bundle = _bundle(training_analyses)
    if bundle is None:
        return insufficient_segment(customer_id, analysis['data_quality'])
    scaled = bundle['scaler'].transform([vector])
    cluster = int(bundle['model'].predict(scaled)[0])
    distances = np.linalg.norm(bundle['model'].cluster_centers_ - scaled[0], axis=1)
    nearest = sorted(float(value) for value in distances)
    separation = 1 - nearest[0] / nearest[1] if len(nearest) > 1 and nearest[1] > 0 else 1
    confidence_score = round(max(0, min(1, separation)), 2)
    confidence = 'High' if confidence_score >= .55 else 'Medium' if confidence_score >= .25 else 'Low'
    segment = bundle['labels'][cluster]
    return {
        'customer_id': customer_id,
        'status': 'available',
        'segment': segment,
        'segment_description': DESCRIPTIONS[segment],
        'confidence': confidence,
        'confidence_score': confidence_score,
        'key_characteristics': _characteristics(analysis),
        'model': {
            'algorithm': 'K-Means', 'clusters': 4, 'features': list(FEATURES),
            'preprocessing': 'StandardScaler', 'random_state': 42, 'trained': True,
            'interpretation': 'Centroids are ordered by estimated stress, with savings rate as a tie-breaker, then named GROWTH through SUPPORT.',
        },
    }
