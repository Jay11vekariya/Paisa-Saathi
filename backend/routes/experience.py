"""Authenticated alerts, guided lending, safe KYC, privacy, and demo APIs."""
from flask import Blueprint, g, jsonify, request
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from db import get_collection
from services.auth import current_identity, issue_token
from services.customer_data import dashboard_for_authenticated, is_synthetic_customer
from services.loan_simulator import simulate_loan
from services.proactive_alerts import alerts_for_customer, update_alert
from services.product_experience import DEMO_SCENARIOS, KYC_DEMO, PRIVACY, RESPONSIBLE_AI


bp = Blueprint('experience', __name__)


def _identity():
    return current_identity(required=True)


def _demo_scenario():
    return getattr(g, 'session_claims', {}).get('demo_scenario')


@bp.get('/alerts')
def alerts():
    cid = _identity()
    return jsonify(alerts_for_customer(cid, _demo_scenario()))


@bp.get('/alerts/<alert_id>')
def alert_detail(alert_id):
    cid = _identity()
    result = alerts_for_customer(cid, _demo_scenario())
    item = next((item for item in result['alerts'] if item['alert_id'] == alert_id), None)
    if item is None: raise NotFound('Alert not found.')
    return jsonify(alert=item)


@bp.post('/alerts/<alert_id>/<action>')
def alert_action(alert_id, action):
    if action not in {'read', 'dismiss', 'mine', 'report'}:
        raise BadRequest('Unsupported alert action.')
    cid = _identity()
    result = update_alert(cid, alert_id, action, _demo_scenario())
    if result is None: raise NotFound('Alert not found.')
    return jsonify(result)


@bp.post('/loan-journey/start')
def loan_start():
    cid = _identity()
    analysis = dashboard_for_authenticated(cid)
    metrics = analysis['metrics']
    return jsonify(customer_id=cid, guidance_type='Financial suitability guidance',
        known_financial_context={'monthly_income': metrics['monthly_income'],
            'monthly_expenses': metrics['monthly_expenses'], 'monthly_surplus': metrics['monthly_savings'],
            'existing_emi': metrics['monthly_emi'], 'emi_burden': metrics['emi_burden'],
            'financial_stress': analysis['financial_stress'], 'financial_profile': analysis['segmentation']},
        purposes=['Education', 'Medical', 'Home', 'Business', 'Personal', 'Other'],
        disclaimer='Prototype suitability guidance only; this is not a credit approval or rejection.')


def _loan_inputs(data):
    try:
        amount, rate, months = float(data.get('loan_amount')), float(data.get('annual_interest_rate')), int(data.get('tenure_months'))
    except (TypeError, ValueError):
        raise BadRequest('Loan amount, interest rate, and tenure must be valid numbers.') from None
    purpose = str(data.get('purpose') or '').strip()
    if amount <= 0 or not 0 <= rate <= 100 or not 1 <= months <= 600 or purpose not in {'Education', 'Medical', 'Home', 'Business', 'Personal', 'Other'}:
        raise BadRequest('Use a valid amount, purpose, 0–100% rate, and 1–600 month tenure.')
    return {'loan_amount': round(amount, 2), 'annual_interest_rate': round(rate, 3),
            'tenure_months': months, 'existing_emi': None, 'purpose': purpose}


@bp.post('/loan-journey/assessment')
def loan_assessment():
    cid = _identity()
    result = simulate_loan(dashboard_for_authenticated(cid), _loan_inputs(request.get_json(silent=True) or {}))
    result['guidance_type'] = 'Financial suitability guidance'
    return jsonify(result)


@bp.get('/kyc/demo')
def kyc_demo():
    _identity()
    return jsonify(KYC_DEMO)


@bp.post('/kyc/demo/complete')
def kyc_complete():
    _identity()
    data = request.get_json(silent=True) or {}
    forbidden_fragments = ('aadhaar', 'aadhar', 'pan', 'document', 'upload', 'biometric', 'fingerprint')
    if any(any(fragment in key.lower() for fragment in forbidden_fragments) for key in data):
        raise BadRequest('Real identity numbers or documents are not accepted in this prototype.')
    required = ('full_name', 'date_of_birth', 'city', 'state', 'pincode', 'identity_type', 'demo_reference')
    if any(not isinstance(data.get(key), str) or not data[key].strip() for key in required):
        raise BadRequest('Complete all synthetic demo fields.')
    if data['identity_type'] not in KYC_DEMO['identity_types']:
        raise BadRequest('Choose a demo identity type.')
    if data['demo_reference'] != KYC_DEMO['masked_demo_id']:
        raise BadRequest('Use only the masked demo reference supplied by Paisa Saathi.')
    return jsonify(status='Demo KYC completed', stored=False, government_verified=False,
                   notice=KYC_DEMO['notice'])


@bp.get('/privacy')
def privacy():
    cid = _identity()
    user = get_collection('users').find_one({'customer_id': cid}, {'_id': 0, 'privacy_controls': 1}) or {}
    payload = {**PRIVACY, 'controls': user.get('privacy_controls', PRIVACY['controls'])}
    return jsonify(payload)


@bp.put('/privacy')
def privacy_update():
    cid = _identity()
    data = request.get_json(silent=True) or {}
    if set(data) != set(PRIVACY['controls']) or any(not isinstance(value, bool) for value in data.values()):
        raise BadRequest('Send all privacy controls as true or false.')
    get_collection('users').update_one({'customer_id': cid}, {'$set': {'privacy_controls': data}})
    return jsonify(controls=data, updated=True)


@bp.get('/responsible-ai')
def responsible_ai():
    _identity()
    return jsonify(RESPONSIBLE_AI)


@bp.get('/demo/scenarios')
def demo_scenarios():
    return jsonify(demo_mode=True, scenarios=[{'scenario_id': key, **value} for key, value in DEMO_SCENARIOS.items()],
                   notice='DEMO MODE uses allowlisted synthetic customers only.')


@bp.post('/demo/session')
def demo_session():
    scenario_id = (request.get_json(silent=True) or {}).get('scenario_id')
    scenario = DEMO_SCENARIOS.get(scenario_id)
    if scenario is None: raise Forbidden('Only allowlisted demo scenarios can be launched.')
    user = get_collection('users').find_one({'customer_id': scenario['customer_id'], 'synthetic': True})
    if user is None: raise NotFound('Synthetic demo customer is unavailable.')
    token = issue_token(user, {'demo_mode': True, 'demo_scenario': scenario.get('demo_scenario'),
                               'scenario_id': scenario_id})
    safe_user = {key: user.get(key) for key in ('customer_id', 'name', 'city', 'language', 'synthetic')}
    return jsonify(token=token, user=safe_user, demo_mode=True, scenario={'scenario_id': scenario_id, **scenario},
                   onboarding_complete=True)


@bp.post('/demo/reset')
def demo_reset():
    cid = _identity()
    if not getattr(g, 'session_claims', {}).get('demo_mode') or not is_synthetic_customer(cid):
        raise Forbidden('Reset Demo is available only inside an allowlisted demo session.')
    get_collection('alerts').update_many({'customer_id': cid}, {'$set': {'status': 'UNREAD'}})
    return jsonify(reset=True, customer_id=cid, notice='Synthetic financial data was not changed.')
