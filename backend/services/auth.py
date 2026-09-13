from datetime import datetime, timedelta, timezone
from functools import wraps
import jwt
from flask import current_app, g, request
from werkzeug.exceptions import Unauthorized, Forbidden


def demo_identity():
    return {'name': 'Rahul Patel', 'mode': 'demo', 'authenticated': False}


def issue_token(user, extra_claims=None):
    now = datetime.now(timezone.utc)
    payload = {'sub': user['customer_id'], 'email': user['email'], 'iat': now,
               'exp': now + timedelta(hours=current_app.config['JWT_EXPIRY_HOURS'])}
    payload.update(extra_claims or {})
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def current_identity(required=False):
    header = request.headers.get('Authorization', '')
    if not header:
        if required:
            raise Unauthorized('Authentication is required.')
        return None
    if not header.startswith('Bearer '):
        raise Unauthorized('Use a Bearer token.')
    try:
        data = jwt.decode(header[7:], current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        g.session_claims = data
        return data['sub']
    except (jwt.InvalidTokenError, KeyError):
        raise Unauthorized('Your session is invalid or has expired.') from None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        g.customer_id = current_identity(required=True)
        return view(*args, **kwargs)
    return wrapped


def assert_current_customer(customer_id):
    identity = current_identity()
    if identity and identity != customer_id:
        raise Forbidden('You can only access your own financial data.')
