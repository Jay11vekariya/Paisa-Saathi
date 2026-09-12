import re
from datetime import date
from math import isfinite
from werkzeug.exceptions import BadRequest

CATEGORIES = {'Salary', 'Food', 'Shopping', 'Transport', 'Bills', 'Rent', 'Education', 'Healthcare', 'Entertainment', 'Investment', 'EMI', 'UPI Transfer', 'Other'}

def customer_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'PS[0-9]{3}', value):
        raise BadRequest('Customer ID must use the format PS001.')
    return value

def validate_transaction(row):
    customer_id(row.get('customer_id'))
    if not isinstance(row.get('transaction_id'), str) or not re.fullmatch(r'PS[0-9]{3}-[0-9]{6}-[0-9]{3}', row['transaction_id']):
        raise ValueError('Invalid transaction ID.')
    amount = row.get('amount')
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not isfinite(amount) or amount <= 0:
        raise ValueError('Transaction amount must be finite and positive.')
    if row.get('type') not in ('credit', 'debit'):
        raise ValueError('Transaction type must be credit or debit.')
    if row.get('category') not in CATEGORIES:
        raise ValueError('Unknown transaction category.')
    value = row.get('date')
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('Date must be YYYY-MM-DD.')
    date.fromisoformat(value)
    for field in ('merchant', 'location', 'payment_method'):
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError(f'{field} is required.')
    return row
