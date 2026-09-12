from flask import Blueprint, jsonify

from services.customer_data import recommendations_for

bp = Blueprint('recommendations', __name__)


@bp.get('/recommendations/<cid>')
def recommendations(cid):
    return jsonify(recommendations_for(cid))
