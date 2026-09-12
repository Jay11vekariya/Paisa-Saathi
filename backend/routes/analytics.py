from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest
from services.customer_data import list_customers, dashboard_for, transactions_for
from services.auth import assert_current_customer

bp = Blueprint('analytics', __name__)

@bp.get('/customers')
def customers():
    return jsonify(customers=list_customers(),source='mongodb',synthetic=True)

@bp.get('/dashboard/<cid>')
def dashboard(cid):
    assert_current_customer(cid)
    return jsonify(dashboard_for(cid))

@bp.get('/financial-health/<cid>')
def health(cid):
    assert_current_customer(cid)
    data = dashboard_for(cid)
    return jsonify(customer_id=cid,**data['financial_health'],period=data['period'],source='mongodb')

@bp.get('/financial-state/<cid>')
def state(cid):
    assert_current_customer(cid)
    return jsonify(customer_id=cid,**dashboard_for(cid)['financial_state'],source='mongodb')

@bp.get('/spending/<cid>')
def spending(cid):
    assert_current_customer(cid)
    data = dashboard_for(cid)
    return jsonify(customer_id=cid,**data['spending'],period=data['period'],source='mongodb')

@bp.get('/transactions/<cid>')
def transactions(cid):
    assert_current_customer(cid)
    try:
        page,limit = int(request.args.get('page',1)),int(request.args.get('limit',20))
    except ValueError:
        raise BadRequest('Page and limit must be integers.') from None
    if page<1 or not 1<=limit<=100:
        raise BadRequest('Page must be positive and limit must be between 1 and 100.')
    return jsonify(transactions_for(cid,page,limit))
