"""Authentication and private-user pipeline tests using the in-memory Mongo adapter."""
import unittest
import mongomock
import copy
from app import create_app
from seed_demo_users import seed_demo_users, demo_email, demo_password
from services.synthetic import generate
from datetime import date

class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'MONGO_URI': '', 'JWT_SECRET_KEY': 'test-secret'})
        self.app.extensions['mongo'] = mongomock.MongoClient()
        self.client = self.app.test_client()
    def register(self, email='rahul@example.com'):
        response = self.client.post('/api/auth/register', json={'full_name':'Rahul Patel','email':email,'password':'secure-pass-1','confirm_password':'secure-pass-1'})
        self.assertEqual(response.status_code, 201); return response.json['token']
    def headers(self, token): return {'Authorization':f'Bearer {token}'}
    def onboard(self, token):
        return self.client.put('/api/profile', headers=self.headers(token), json={'full_name':'Rahul Patel','age':29,'city':'Rajkot','language':'Gujarati','employment_type':'Salaried','monthly_income':75000,'monthly_expenses':42000,'monthly_emi':8000,'account_balance':150000})
    def test_register_login_baseline_and_recommendations(self):
        token = self.register(); self.assertEqual(self.onboard(token).status_code, 200)
        me = self.client.get('/api/auth/me', headers=self.headers(token)); self.assertEqual(me.status_code, 200)
        dashboard = self.client.get('/api/dashboard', headers=self.headers(token)); self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.json['metrics']['monthly_income'], 75000)
        self.assertIn(dashboard.json['financial_state']['state'], {'GROWTH','NORMAL','CAUTION','SUPPORT'})
        self.assertEqual(self.client.get('/api/recommendations', headers=self.headers(token)).status_code, 200)
        self.assertEqual(self.client.post('/api/auth/login', json={'email':'rahul@example.com','password':'wrong'}).status_code, 401)
        self.assertEqual(self.client.post('/api/auth/register', json={'full_name':'Other User','email':'rahul@example.com','password':'secure-pass-1','confirm_password':'secure-pass-1'}).status_code, 409)
    def test_transaction_and_user_isolation(self):
        first=self.register('first@example.com'); self.onboard(first)
        second=self.register('second@example.com'); self.onboard(second)
        created=self.client.post('/api/transactions',headers=self.headers(first),json={'date':'2026-09-01','type':'expense','category':'Food','amount':500,'merchant':'Cafe','location':'Rajkot'})
        self.assertEqual(created.status_code,201)
        self.assertEqual(self.client.get('/api/transactions',headers=self.headers(first)).json['total'],1)
        self.assertEqual(self.client.get('/api/transactions',headers=self.headers(second)).json['total'],0)
        first_id=self.client.get('/api/auth/me',headers=self.headers(first)).json['user']['customer_id']
        self.assertEqual(self.client.get('/api/dashboard/'+first_id,headers=self.headers(second)).status_code,403)
    def test_synthetic_demo_user_uses_the_same_login_and_jwt_routes(self):
        data = generate(date(2026, 9, 12))
        for name, rows in data.items(): self.app.extensions['mongo'].paisaSaathiDB[name].insert_many(copy.deepcopy(rows))
        with self.app.app_context():
            first = seed_demo_users(); second = seed_demo_users()
        self.assertEqual(first['created'], len(data['users']))
        self.assertEqual(second['already_existed'], len(data['users']))
        login = self.client.post('/api/auth/login', json={'email':demo_email('PS001'), 'password':demo_password('PS001')})
        self.assertEqual(login.status_code, 200); self.assertEqual(login.json['user']['customer_id'], 'PS001')
        headers = self.headers(login.json['token'])
        self.assertEqual(self.client.get('/api/dashboard', headers=headers).json['customer']['customer_id'], 'PS001')
        self.assertEqual(self.client.get('/api/financial-health', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/recommendations', headers=headers).status_code, 200)
        transactions = self.client.get('/api/transactions', headers=headers).json
        self.assertTrue(transactions['transactions'])
        self.assertTrue(all(row['customer_id'] == 'PS001' for row in transactions['transactions']))
    def test_multiple_demo_jwts_resolve_their_own_customer_data(self):
        data = generate(date(2026, 9, 12))
        for name, rows in data.items(): self.app.extensions['mongo'].paisaSaathiDB[name].insert_many(copy.deepcopy(rows))
        with self.app.app_context(): seed_demo_users()
        seen = {}
        for customer_id in ('PS001', 'PS003', 'PS004'):
            login = self.client.post('/api/auth/login', json={'email':demo_email(customer_id), 'password':demo_password(customer_id)})
            self.assertEqual(login.status_code, 200)
            headers = self.headers(login.json['token'])
            self.assertEqual(self.client.get('/api/auth/me', headers=headers).json['user']['customer_id'], customer_id)
            dashboard = self.client.get('/api/dashboard', headers=headers).json
            recommendations = self.client.get('/api/recommendations', headers=headers).json
            transactions = self.client.get('/api/transactions', headers=headers).json
            self.assertEqual(dashboard['customer']['customer_id'], customer_id)
            self.assertEqual(recommendations['customer']['customer_id'], customer_id)
            self.assertEqual(transactions['customer_id'], customer_id)
            seen[customer_id] = dashboard['financial_state']['state']
        self.assertEqual(seen, {'PS001':'GROWTH', 'PS003':'CAUTION', 'PS004':'SUPPORT'})

if __name__ == '__main__': unittest.main()
