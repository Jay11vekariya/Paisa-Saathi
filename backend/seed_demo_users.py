"""Idempotently attach demo credentials to existing synthetic customer records."""
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from app import create_app
from db import get_collection, DatabaseUnavailable
from pymongo.errors import PyMongoError

def demo_email(customer_id): return f'{customer_id.lower()}@demo.paisasaathi.local'
def demo_password(customer_id): return f'Paisa@{customer_id}'

def seed_demo_users():
    users = get_collection('users')
    created = existed = updated = 0
    for customer in users.find({'synthetic':True}, {'customer_id':1, 'email':1, 'password_hash':1, 'role':1, 'created_at':1}):
        cid = customer['customer_id']; email = demo_email(cid)
        # Never overwrite an unexpected credential-bearing record.
        if customer.get('email') and customer['email'] != email:
            existed += 1; continue
        changes = {}
        if not customer.get('email'): changes['email'] = email
        if not customer.get('password_hash'): changes['password_hash'] = generate_password_hash(demo_password(cid))
        if not customer.get('role'): changes['role'] = 'demo'
        if not customer.get('created_at'): changes['created_at'] = datetime.now(timezone.utc)
        if changes:
            users.update_one({'_id':customer['_id']}, {'$set':changes})
            created += 1 if not customer.get('email') else 0
            updated += 1 if customer.get('email') else 0
        else: existed += 1
    return {'created':created, 'already_existed':existed, 'updated':updated, 'failed':0}

def main():
    app = create_app()
    try:
        with app.app_context(): result = seed_demo_users()
    except (DatabaseUnavailable, PyMongoError):
        print('Demo-user seed failed. Check MongoDB configuration and connectivity.'); return 1
    print('Created: {created}\nAlready existed: {already_existed}\nUpdated: {updated}\nFailed: {failed}'.format(**result)); return 0

if __name__ == '__main__': raise SystemExit(main())
