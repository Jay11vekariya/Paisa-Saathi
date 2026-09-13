"""Tests for proactive intervention and hackathon experience APIs."""
import copy
import unittest
from datetime import date

import mongomock

from app import create_app
from seed_demo_users import demo_email, demo_password, seed_demo_users
from services.synthetic import generate


class ExperienceApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'MONGO_URI': '',
                               'JWT_SECRET_KEY': 'test-secret-at-least-thirty-two-bytes'})
        self.app.extensions['mongo'] = mongomock.MongoClient()
        for name, rows in generate(date(2026, 9, 12)).items():
            self.app.extensions['mongo'].paisaSaathiDB[name].insert_many(copy.deepcopy(rows))
        with self.app.app_context(): seed_demo_users()
        self.client = self.app.test_client()

    def login(self, cid):
        result = self.client.post('/api/auth/login', json={
            'email': demo_email(cid), 'password': demo_password(cid)}).json
        return {'Authorization': f"Bearer {result['token']}"}

    def test_alert_generation_stress_intervention_and_customer_isolation(self):
        ramesh = self.client.get('/api/alerts', headers=self.login('PS003'))
        self.assertEqual(ramesh.status_code, 200)
        stress = next(item for item in ramesh.json['alerts'] if item['type'] == 'FINANCIAL_STRESS')
        self.assertEqual(stress['customer_id'], 'PS003')
        self.assertIn(stress['severity'], {'HIGH', 'CRITICAL'})
        self.assertIn('support', stress['why_it_matters'].lower())
        self.assertIn('Pause new borrowing', stress['safer_alternative'])
        rahul = self.client.get(f"/api/alerts/{stress['alert_id']}", headers=self.login('PS001'))
        self.assertEqual(rahul.status_code, 404)
        recommendations = self.client.get('/api/recommendations', headers=self.login('PS004')).json
        self.assertFalse(any(item['category'] == 'Loan' for item in recommendations['recommendations']))
        self.assertTrue(any(item['category'] == 'Loan' for item in recommendations['not_recommended']))

    def test_alert_actions_keep_audit_and_fraud_demo_is_claim_scoped(self):
        session = self.client.post('/api/demo/session', json={'scenario_id': 'aman-fraud'}).json
        headers = {'Authorization': f"Bearer {session['token']}"}
        alerts = self.client.get('/api/alerts', headers=headers).json
        fraud = next(item for item in alerts['alerts'] if item['source_engine'] == 'demo_scenario_fixture')
        self.assertIn('₹52,000', fraud['message'])
        action = self.client.post(f"/api/alerts/{fraud['alert_id']}/report", headers=headers)
        self.assertEqual(action.json['status'], 'REPORTED_SUSPICIOUS')
        stored = self.app.extensions['mongo'].paisaSaathiDB.alerts.find_one({'alert_id': fraud['alert_id']})
        self.assertEqual(stored['customer_id'], 'PS004')
        self.assertEqual(len(stored['audit']), 1)
        normal = self.client.get('/api/alerts', headers=self.login('PS004')).json
        self.assertFalse(any(item['source_engine'] == 'demo_scenario_fixture' for item in normal['alerts']))

    def test_loan_journey_reuses_verified_simulator(self):
        headers = self.login('PS001')
        start = self.client.post('/api/loan-journey/start', headers=headers)
        self.assertEqual(start.status_code, 200)
        self.assertEqual(start.json['known_financial_context']['monthly_income'], 75000)
        result = self.client.post('/api/loan-journey/assessment', headers=headers, json={
            'loan_amount': 200000, 'purpose': 'Business', 'annual_interest_rate': 8,
            'tenure_months': 12}).json
        self.assertEqual(result['customer_id'], 'PS001')
        self.assertEqual(result['loan_inputs']['purpose'], 'Business')
        self.assertIn('not a loan approval', result['disclaimer'].lower())

    def test_kyc_demo_rejects_real_identity_fields_and_stores_nothing(self):
        headers = self.login('PS001')
        info = self.client.get('/api/kyc/demo', headers=headers)
        self.assertTrue(info.json['demo'])
        rejected = self.client.post('/api/kyc/demo/complete', headers=headers, json={
            'full_name': 'Demo Person', 'date_of_birth': '1990-01-01', 'city': 'Ahmedabad',
            'state': 'Gujarat', 'pincode': '380001', 'identity_type': 'Aadhaar (Demo)',
            'demo_reference': 'XXXX-XXXX-1234', 'aadhaar': '1234'})
        self.assertEqual(rejected.status_code, 400)
        accepted = self.client.post('/api/kyc/demo/complete', headers=headers, json={
            'full_name': 'Demo Person', 'date_of_birth': '1990-01-01', 'city': 'Ahmedabad',
            'state': 'Gujarat', 'pincode': '380001', 'identity_type': 'Aadhaar (Demo)',
            'demo_reference': 'XXXX-XXXX-1234'})
        self.assertFalse(accepted.json['stored'])
        self.assertEqual(accepted.json['status'], 'Demo KYC completed')

    def test_responsible_ai_privacy_and_demo_allowlist(self):
        headers = self.login('PS001')
        responsible = self.client.get('/api/responsible-ai', headers=headers)
        self.assertEqual(responsible.status_code, 200)
        self.assertIn('NO PREDATORY NUDGING', [item['name'] for item in responsible.json['principles']])
        privacy = self.client.get('/api/privacy', headers=headers)
        self.assertIn('synthetic/demo', privacy.json['prototype_notice'])
        scenarios = self.client.get('/api/demo/scenarios').json
        self.assertEqual(len(scenarios['scenarios']), 4)
        expected_customers = {'rahul-growth':'PS001', 'ramesh-stress':'PS003',
                              'aman-fraud':'PS004', 'ramesh-gujarati':'PS003'}
        for scenario_id, customer_id in expected_customers.items():
            with self.subTest(scenario_id=scenario_id):
                launched = self.client.post('/api/demo/session', json={'scenario_id': scenario_id})
                self.assertEqual(launched.status_code, 200)
                self.assertEqual(launched.json['user']['customer_id'], customer_id)
                self.assertTrue(launched.json['demo_mode'])
        self.assertEqual(self.client.post('/api/demo/session', json={'scenario_id': 'PS999'}).status_code, 403)
        normal_reset = self.client.post('/api/demo/reset', headers=headers)
        self.assertEqual(normal_reset.status_code, 403)


if __name__ == '__main__': unittest.main()
