"""Financial-stress, K-Means segmentation, and recommendation integration tests."""
import copy
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import mongomock

from app import create_app
from seed_demo_users import demo_email, demo_password, seed_demo_users
from services.financial_health import analyse
from services.financial_stress import calculate_stress
from services.recommendations import recommend
from services.segmentation import FEATURES, SEGMENTS, feature_vector, segment_customer
from services.synthetic import generate


class InsightTests(unittest.TestCase):
    def setUp(self):
        self.data = generate(date(2026, 9, 12))
        self.analyses = []
        for user in self.data['users']:
            profile = next(row for row in self.data['financial_profiles'] if row['customer_id'] == user['customer_id'])
            transactions = [row for row in self.data['transactions'] if row['customer_id'] == user['customer_id']]
            self.analyses.append(analyse(user, transactions, profile))

    def test_stress_is_bounded_explainable_and_distinct(self):
        healthy, caution, support = self.analyses[0], self.analyses[2], self.analyses[3]
        self.assertEqual((healthy['financial_stress']['stress_level'], caution['financial_stress']['stress_level'], support['financial_stress']['stress_level']),
                         ('LOW', 'HIGH', 'CRITICAL'))
        for analysis in self.analyses:
            stress = analysis['financial_stress']
            self.assertTrue(0 <= stress['stress_score'] <= 100)
            self.assertEqual(len(stress['factors']), 7)
            self.assertTrue(all({'name', 'impact', 'value', 'explanation', 'weight', 'points'} <= factor.keys() for factor in stress['factors']))

    def test_insufficient_history_does_not_invent_stress_or_segment(self):
        analysis = self.analyses[0]
        quality = {'transaction_count': 0, 'observed_months': 0, 'baseline_only': True}
        stress = calculate_stress('PS999', analysis['metrics'], quality)
        incomplete = {**analysis, 'customer': {**analysis['customer'], 'customer_id': 'PS999'},
                      'financial_stress': stress, 'data_quality': quality}
        segment = segment_customer(incomplete, self.analyses)
        self.assertEqual(stress['status'], 'insufficient_data')
        self.assertIsNone(stress['stress_score'])
        self.assertEqual(segment['status'], 'insufficient_data')
        self.assertIsNone(segment['segment'])

    def test_kmeans_uses_scaled_features_and_four_named_segments(self):
        results = [segment_customer(analysis, self.analyses) for analysis in self.analyses]
        self.assertEqual({result['segment'] for result in results}, set(SEGMENTS))
        self.assertEqual(len(feature_vector(self.analyses[0])), len(FEATURES))
        self.assertTrue(all(result['model']['algorithm'] == 'K-Means' for result in results))
        self.assertTrue(all(result['model']['clusters'] == 4 for result in results))
        self.assertTrue(all(result['model']['preprocessing'] == 'StandardScaler' for result in results))

    def test_recommendations_consume_stress_and_keep_why_not_this(self):
        analysis = self.analyses[3]
        segment = segment_customer(analysis, self.analyses)
        result = recommend(analysis['metrics'], analysis['financial_state'], self.data['products'], analysis['financial_stress'], segment)
        self.assertIn('financial_stress', result['engine']['signals_used'])
        self.assertIn('customer_segment', result['engine']['signals_used'])
        loans = [item for item in result['not_recommended'] if item['product']['category'] == 'Loan']
        self.assertTrue(loans)
        self.assertTrue(loans[0]['why_not_this'])
        self.assertTrue(loans[0]['safer_alternative']['action'])
        self.assertTrue(any('financial stress' in condition.lower() for condition in loans[0]['rejection_conditions']))


class InsightApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'MONGO_URI': '', 'JWT_SECRET_KEY': 'test-secret-at-least-thirty-two-bytes'})
        self.app.extensions['mongo'] = mongomock.MongoClient()
        self.client = self.app.test_client()
        data = generate(date(2026, 9, 12))
        for name, rows in data.items():
            self.app.extensions['mongo'].paisaSaathiDB[name].insert_many(copy.deepcopy(rows))
        with self.app.app_context():
            seed_demo_users()

    def login(self, customer_id):
        response = self.client.post('/api/auth/login', json={'email': demo_email(customer_id), 'password': demo_password(customer_id)})
        self.assertEqual(response.status_code, 200)
        return {'Authorization': f"Bearer {response.json['token']}"}

    def test_authenticated_insight_endpoints_are_customer_isolated(self):
        headers = self.login('PS001')
        stress = self.client.get('/api/financial-stress', headers=headers)
        segment = self.client.get('/api/segmentation', headers=headers)
        repeated_dashboard = self.client.get('/api/dashboard', headers=headers)
        repeated_dashboard_again = self.client.get('/api/dashboard', headers=headers)
        self.assertEqual((stress.status_code, segment.status_code), (200, 200))
        self.assertEqual((repeated_dashboard.status_code, repeated_dashboard_again.status_code), (200, 200))
        self.assertEqual((stress.json['customer_id'], segment.json['customer_id']), ('PS001', 'PS001'))
        self.assertEqual(self.client.get('/api/financial-stress/PS003', headers=headers).status_code, 403)
        self.assertEqual(self.client.get('/api/segmentation/PS003', headers=headers).status_code, 403)
        self.assertEqual(self.client.get('/api/financial-stress').status_code, 401)

    def test_demo_profiles_and_new_user_empty_state(self):
        expected = {'PS001': ('LOW', 'GROWTH'), 'PS003': ('HIGH', 'CAUTION'), 'PS004': ('CRITICAL', 'SUPPORT')}
        for customer_id, values in expected.items():
            headers = self.login(customer_id)
            dashboard = self.client.get('/api/dashboard', headers=headers).json
            self.assertEqual((dashboard['financial_stress']['stress_level'], dashboard['segmentation']['segment']), values)
        registered = self.client.post('/api/auth/register', json={'full_name':'New User','email':'new-user@example.test','password':'secure-pass-1','confirm_password':'secure-pass-1'})
        headers = {'Authorization': f"Bearer {registered.json['token']}"}
        profile = {'full_name':'New User','age':30,'city':'Rajkot','language':'English','employment_type':'Salaried',
                   'monthly_income':50000,'monthly_expenses':30000,'monthly_emi':0,'account_balance':50000}
        self.assertEqual(self.client.put('/api/profile', headers=headers, json=profile).status_code, 200)
        dashboard = self.client.get('/api/dashboard', headers=headers).json
        self.assertEqual(dashboard['financial_stress']['status'], 'insufficient_data')
        self.assertEqual(dashboard['segmentation']['status'], 'insufficient_data')
        entries = [
            ('2026-08-01','income','Salary',50000), ('2026-08-05','expense','Rent',15000),
            ('2026-08-12','expense','Food',8000), ('2026-09-01','income','Salary',50000),
            ('2026-09-05','expense','Rent',15000), ('2026-09-12','expense','Food',7500),
        ]
        for entry_date, tx_type, category, amount in entries:
            response = self.client.post('/api/transactions', headers=headers, json={
                'date':entry_date, 'type':tx_type, 'category':category, 'amount':amount,
                'merchant':'User-entered history', 'location':'Rajkot',
            })
            self.assertEqual(response.status_code, 201)
        dashboard = self.client.get('/api/dashboard', headers=headers).json
        self.assertEqual(dashboard['financial_stress']['status'], 'available')
        self.assertEqual(dashboard['segmentation']['status'], 'available')

    def test_concurrent_dashboard_analysis_is_stable(self):
        headers = self.login('PS003')
        def fetch_dashboard(_):
            with self.app.test_client() as client:
                response = client.get('/api/dashboard', headers=headers)
                return response.status_code, response.json.get('segmentation', {}).get('segment')
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(fetch_dashboard, range(4)))
        self.assertEqual(results, [(200, 'CAUTION')] * 4)


if __name__ == '__main__':
    unittest.main()
