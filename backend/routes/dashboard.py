from flask import Blueprint, jsonify
from services.auth import current_identity
from services.customer_data import dashboard_for_authenticated
from services.demo import DEMO

bp = Blueprint('dashboard', __name__)

@bp.get('/dashboard')
def dashboard():
    cid = current_identity()
    return jsonify(dashboard_for_authenticated(cid) if cid else DEMO['dashboard'])

@bp.get('/financial-health')
def financial_health():
    cid = current_identity()
    if cid:
        data = dashboard_for_authenticated(cid)
        return jsonify(customer_id=cid, **data['financial_health'], period=data['period'], source=data['source'])
    return jsonify(**DEMO['dashboard']['health'], source='demo')

