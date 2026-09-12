from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest, Forbidden

from services.auth import current_identity
from services.customer_data import dashboard_for_authenticated, ledger_for_authenticated
from services.anomaly_detection import detect_anomalies
from services.loan_simulator import simulate_loan


bp = Blueprint('insights', __name__)


def _identity_for(cid=None):
    identity = current_identity(required=True)
    if cid is not None and cid != identity:
        raise Forbidden('You can only access your own financial data.')
    return identity


@bp.get('/financial-stress')
def financial_stress():
    cid = _identity_for()
    return jsonify(dashboard_for_authenticated(cid)['financial_stress'])


@bp.get('/financial-stress/<cid>')
def financial_stress_for_customer(cid):
    _identity_for(cid)
    return jsonify(dashboard_for_authenticated(cid)['financial_stress'])


@bp.get('/segmentation')
def segmentation():
    cid = _identity_for()
    return jsonify(dashboard_for_authenticated(cid)['segmentation'])


@bp.get('/segmentation/<cid>')
def segmentation_for_customer(cid):
    _identity_for(cid)
    return jsonify(dashboard_for_authenticated(cid)['segmentation'])


@bp.get('/anomalies')
def anomalies():
    cid = _identity_for()
    customer, transactions, profile = ledger_for_authenticated(cid)
    return jsonify(detect_anomalies(customer, transactions, profile))


@bp.post('/loan-simulator')
def loan_simulator():
    cid = _identity_for()
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get('loan_amount'))
        rate = float(data.get('annual_interest_rate'))
        months = int(data.get('tenure_months'))
        existing = data.get('existing_emi')
        existing = None if existing in (None, '') else float(existing)
    except (TypeError, ValueError):
        raise BadRequest('Loan amount, interest rate, and tenure must be valid numbers.') from None
    if amount <= 0 or not 0 <= rate <= 100 or not 1 <= months <= 600 or (existing is not None and existing < 0):
        raise BadRequest('Use a positive loan amount, 0–100% interest, and a tenure of 1–600 months.')
    inputs = {'loan_amount': round(amount, 2), 'annual_interest_rate': round(rate, 3),
              'tenure_months': months, 'existing_emi': existing,
              'purpose': str(data.get('purpose') or '').strip()[:120] or None}
    return jsonify(simulate_loan(dashboard_for_authenticated(cid), inputs))
