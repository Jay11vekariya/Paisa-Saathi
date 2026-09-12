from flask import Blueprint, jsonify
from services.demo import DEMO

bp = Blueprint('transactions', __name__)

@bp.get('/transactions')
def transactions():
    return jsonify(transactions=DEMO['transactions'], source='demo')
