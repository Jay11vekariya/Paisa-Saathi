from datetime import date
from uuid import uuid4
from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest, Forbidden
from services.auth import current_identity
from services.customer_data import transactions_for_authenticated, is_synthetic_customer
from utils.validation import CATEGORIES
from db import get_collection
from services.demo import DEMO

bp = Blueprint('transactions', __name__)

@bp.route('/transactions', methods=['GET', 'POST'])
def transactions():
    cid = current_identity()
    if request.method == 'GET':
        if not cid: return jsonify(transactions=DEMO['transactions'], source='demo')
        try: page, limit = int(request.args.get('page',1)), int(request.args.get('limit',20))
        except ValueError: raise BadRequest('Page and limit must be integers.') from None
        if page < 1 or not 1 <= limit <= 100: raise BadRequest('Page must be positive and limit must be between 1 and 100.')
        return jsonify(transactions_for_authenticated(cid, page, limit))
    if not cid: return jsonify(error='Authentication is required.'), 401
    if is_synthetic_customer(cid): raise Forbidden('Demo transactions are read-only.')
    data = request.get_json(silent=True) or {}; tx_type = data.get('type')
    normalized_type = 'credit' if tx_type == 'income' else 'debit' if tx_type == 'expense' else None
    if normalized_type is None or data.get('category') not in CATEGORIES: raise BadRequest('Use a valid transaction type and category.')
    try: amount=float(data.get('amount')); date.fromisoformat(data.get('date',''))
    except (TypeError, ValueError): raise BadRequest('Amount and date are invalid.') from None
    if amount <= 0: raise BadRequest('Amount must be positive.')
    tx = {'customer_id':cid, 'transaction_id':f'{cid}-{uuid4().hex[:9]}', 'date':data['date'], 'type':normalized_type, 'category':data['category'], 'amount':round(amount,2), 'merchant':str(data.get('merchant') or 'Not specified').strip(), 'location':str(data.get('location') or 'Not specified').strip(), 'payment_method':'Manual entry', 'synthetic':False}
    get_collection('transactions').insert_one(tx)
    return jsonify(transaction={key:value for key,value in tx.items() if key not in {'synthetic', '_id'}}), 201
