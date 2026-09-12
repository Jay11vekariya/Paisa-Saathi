from datetime import date
import re
from flask import Blueprint, jsonify, request, g
from pymongo.errors import DuplicateKeyError
from werkzeug.exceptions import BadRequest, Conflict, Unauthorized, Forbidden
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_collection
from services.auth import demo_identity, issue_token, login_required

bp = Blueprint('auth', __name__)
LANGUAGES = {'English', 'Hindi', 'Gujarati', 'Hinglish'}
EMPLOYMENT_TYPES = {'Salaried', 'Self-employed', 'Business owner', 'Student', 'Retired', 'Other'}

def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict): raise BadRequest('Send a JSON object.')
    return data
def text(data, field, minimum=1):
    value = data.get(field, '')
    if not isinstance(value, str) or len(value.strip()) < minimum: raise BadRequest(f'{field.replace("_", " ").title()} is required.')
    return value.strip()
def number(data, field, allow_zero=True):
    value = data.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0 or (not allow_zero and value == 0): raise BadRequest(f'{field.replace("_", " ").title()} must be a valid amount.')
    return round(float(value), 2)
def user_view(user):
    return {key:user.get(key) for key in ('customer_id','name','email','role','synthetic','age','city','language','employment_type','monthly_income','monthly_expenses','monthly_emi','account_balance')}
def new_customer_id():
    ids = [int(row['customer_id'][2:]) for row in get_collection('users').find({'customer_id': {'$regex': '^PS[0-9]+$'}}, {'customer_id':1})]
    return f'PS{(max(ids) if ids else 0)+1:03d}'

@bp.post('/auth/demo')
def demo(): return jsonify(demo_identity())
@bp.post('/auth/register')
def register():
    data = body(); name = text(data, 'full_name', 2); email = text(data, 'email', 5).lower(); password = text(data, 'password', 8)
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email): raise BadRequest('Enter a valid email address.')
    if password != data.get('confirm_password'): raise BadRequest('Passwords do not match.')
    if get_collection('users').find_one({'email':email}): raise Conflict('An account already exists for that email address.')
    user = {'customer_id': new_customer_id(), 'name': name, 'email': email, 'password_hash': generate_password_hash(password), 'synthetic': False, 'onboarding_complete': False}
    try: get_collection('users').insert_one(user)
    except DuplicateKeyError: raise Conflict('An account already exists for that email address.') from None
    return jsonify(token=issue_token(user), user=user_view(user), onboarding_complete=False), 201
@bp.post('/auth/login')
def login():
    data = body(); email = text(data, 'email', 5).lower(); password = text(data, 'password', 1)
    user = get_collection('users').find_one({'email':email, 'password_hash': {'$exists': True}})
    if user is None or not check_password_hash(user.get('password_hash',''), password): raise Unauthorized('Incorrect email or password.')
    return jsonify(token=issue_token(user), user=user_view(user), onboarding_complete=bool(user.get('synthetic') or user.get('onboarding_complete')))
@bp.get('/auth/me')
@login_required
def me():
    user = get_collection('users').find_one({'customer_id':g.customer_id})
    if user is None: raise Unauthorized('Account no longer exists.')
    return jsonify(user=user_view(user), onboarding_complete=bool(user.get('synthetic') or user.get('onboarding_complete')))
@bp.post('/auth/logout')
def logout(): return jsonify(logged_out=True)
@bp.get('/profile')
@login_required
def profile():
    user = get_collection('users').find_one({'customer_id':g.customer_id})
    if user is None: raise Unauthorized('Account no longer exists.')
    return jsonify(profile=user_view(user), onboarding_complete=bool(user.get('synthetic') or user.get('onboarding_complete')))
@bp.put('/profile')
@login_required
def save_profile():
    if get_collection('users').find_one({'customer_id':g.customer_id, 'synthetic':True}):
        raise Forbidden('Demo profiles are read-only.')
    data = body()
    try: age = int(data.get('age'))
    except (TypeError, ValueError): raise BadRequest('Age must be a whole number.') from None
    if not 18 <= age <= 120: raise BadRequest('Age must be between 18 and 120.')
    language = text(data, 'language'); employment_type = text(data, 'employment_type')
    if language not in LANGUAGES or employment_type not in EMPLOYMENT_TYPES: raise BadRequest('Choose a supported language and employment type.')
    update = {'name': text(data, 'full_name', 2), 'age':age, 'city':text(data, 'city', 2), 'language':language, 'employment_type':employment_type, 'monthly_income':number(data, 'monthly_income', False), 'monthly_expenses':number(data, 'monthly_expenses'), 'monthly_emi':number(data, 'monthly_emi'), 'account_balance':number(data, 'account_balance'), 'onboarding_complete':True}
    get_collection('users').update_one({'customer_id':g.customer_id, 'synthetic': {'$ne':True}}, {'$set':update})
    profile_doc = {'customer_id':g.customer_id, 'opening_balance':update['account_balance'], 'period_start':date.today().strftime('%Y-%m'), 'period_end':date.today().strftime('%Y-%m'), 'baseline': {key:update[key] for key in ('monthly_income','monthly_expenses','monthly_emi','account_balance')}}
    get_collection('customer_profiles').update_one({'customer_id':g.customer_id}, {'$set':profile_doc}, upsert=True)
    user = get_collection('users').find_one({'customer_id':g.customer_id})
    return jsonify(profile=user_view(user), onboarding_complete=True)
