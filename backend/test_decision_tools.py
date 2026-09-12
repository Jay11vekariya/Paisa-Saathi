"""Focused tests for anomaly indicators and the loan impact simulator."""
import copy
import unittest
from datetime import date

import mongomock

from app import create_app
from seed_demo_users import demo_email, demo_password, seed_demo_users
from services.anomaly_detection import detect_anomalies
from services.financial_health import analyse
from services.loan_simulator import simulate_loan
from services.segmentation import segment_customer
from services.synthetic import generate


class DecisionToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate(date(2026, 9, 12))
        cls.analyses = []
        for user in cls.data['users']:
            profile = next(item for item in cls.data['financial_profiles'] if item['customer_id'] == user['customer_id'])
            rows = [item for item in cls.data['transactions'] if item['customer_id'] == user['customer_id']]
            cls.analyses.append(analyse(user, rows, profile))
        for analysis in cls.analyses:
            analysis['segmentation'] = segment_customer(analysis, cls.analyses)

    def analysis(self, customer_id):
        return next(item for item in self.analyses if item['customer']['customer_id'] == customer_id)

    def transactions(self, customer_id):
        return [item for item in self.data['transactions'] if item['customer_id'] == customer_id]

    def test_demo_anomaly_results_are_explainable(self):
        for customer_id in ('PS001', 'PS003', 'PS004'):
            analysis = self.analysis(customer_id)
            result = detect_anomalies(analysis['customer'], self.transactions(customer_id), {})
            self.assertEqual(result['status'], 'available')
            self.assertEqual(result['customer_id'], customer_id)
            for alert in result['recent_anomalies']:
                self.assertTrue({'anomaly_id', 'transaction_id', 'severity', 'anomaly_type', 'explanation',
                                 'confidence', 'recommended_action', 'detected_signals'} <= alert.keys())
                self.assertNotIn('proof of fraud', alert['explanation'].lower())
        support = detect_anomalies(self.analysis('PS004')['customer'], self.transactions('PS004'), {})
        self.assertIn('EMI_PAYMENT_GAP', {item['anomaly_type'] for item in support['recent_anomalies']})

    def test_large_new_transaction_is_detected_without_calling_it_fraud(self):
        customer_id = 'PS001'
        rows = copy.deepcopy(self.transactions(customer_id))
        rows.append({'transaction_id':'PS001-OUTLIER', 'customer_id':customer_id, 'date':'2026-08-28',
                     'type':'debit', 'category':'Shopping', 'amount':100000, 'merchant':'New merchant',
                     'location':'Ahmedabad', 'payment_method':'UPI', 'synthetic':True})
        result = detect_anomalies(self.analysis(customer_id)['customer'], rows, {})
        kinds = {item['anomaly_type'] for item in result['recent_anomalies']}
        self.assertIn('UNUSUALLY_LARGE_TRANSACTION', kinds)
        self.assertIn('UNUSUAL_MERCHANT', kinds)
        self.assertIn('not proof', result['explanation'].lower())

    def test_insufficient_history_returns_no_fake_anomalies(self):
        analysis = self.analysis('PS001')
        result = detect_anomalies(analysis['customer'], self.transactions('PS001')[:5], {})
        self.assertEqual(result['status'], 'insufficient_data')
        self.assertEqual(result['recent_anomalies'], [])
        self.assertTrue(result['missing_information'])

    def test_safe_caution_high_and_critical_loan_scenarios(self):
        analysis = self.analysis('PS001')
        expected = [(50000, 'SAFE'), (500000, 'CAUTION'), (1200000, 'HIGH IMPACT'), (3000000, 'CRITICAL')]
        for amount, level in expected:
            result = simulate_loan(analysis, {'loan_amount':amount, 'annual_interest_rate':10,
                                               'tenure_months':60, 'existing_emi':None, 'purpose':'Test'})
            self.assertEqual(result['impact_level'], level)
            self.assertGreater(result['emi'], 0)
            self.assertTrue(result['key_impacts'])
            self.assertIn('not a loan approval', result['disclaimer'].lower())


class DecisionToolApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'MONGO_URI': '',
                               'JWT_SECRET_KEY': 'test-secret-at-least-thirty-two-bytes'})
        self.app.extensions['mongo'] = mongomock.MongoClient()
        data = generate(date(2026, 9, 12))
        for name, rows in data.items():
            self.app.extensions['mongo'].paisaSaathiDB[name].insert_many(copy.deepcopy(rows))
        with self.app.app_context():
            seed_demo_users()

    def login(self, customer_id):
        response = self.app.test_client().post('/api/auth/login', json={
            'email': demo_email(customer_id), 'password': demo_password(customer_id)})
        return {'Authorization': f"Bearer {response.json['token']}"}

    def test_jwt_identity_controls_anomalies_and_loan_snapshot(self):
        headers = self.login('PS001')
        client = self.app.test_client()
        anomalies = client.get('/api/anomalies?customer_id=PS003', headers=headers)
        loan = client.post('/api/loan-simulator?customer_id=PS003', headers=headers, json={
            'loan_amount': 50000, 'annual_interest_rate': 10, 'tenure_months': 60})
        self.assertEqual((anomalies.status_code, loan.status_code), (200, 200))
        self.assertEqual((anomalies.json['customer_id'], loan.json['customer_id']), ('PS001', 'PS001'))
        self.assertEqual(client.get('/api/anomalies').status_code, 401)
        self.assertEqual(client.post('/api/loan-simulator', json={}).status_code, 401)


if __name__ == '__main__':
    unittest.main()
