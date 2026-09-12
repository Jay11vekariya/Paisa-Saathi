from flask import Blueprint, jsonify
from werkzeug.exceptions import Forbidden

from services.auth import current_identity
from services.customer_data import dashboard_for_authenticated


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
