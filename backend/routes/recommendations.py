from flask import Blueprint, jsonify

from services.customer_data import recommendations_for, recommendations_for_authenticated
from services.auth import assert_current_customer, current_identity

bp = Blueprint('recommendations', __name__)


@bp.get('/recommendations/<cid>')
def recommendations(cid):
    assert_current_customer(cid)
    return jsonify(recommendations_for(cid))

@bp.get('/recommendations')
def current_recommendations():
    cid = current_identity(required=True)
    return jsonify(recommendations_for_authenticated(cid))
