import unittest

from app import create_app
from db import DatabaseUnavailable, get_collection

class ApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'MONGO_URI': ''})
        self.client = self.app.test_client()

    def test_demo_contracts(self):
        self.assertEqual(self.client.get('/api/health').json['status'], 'ok')
        dashboard = self.client.get('/api/dashboard').json
        self.assertEqual(dashboard['income'] - dashboard['spending'], dashboard['savings'])
        self.assertEqual(sum(c['amount'] for c in dashboard['categories']), dashboard['spending'])
        self.assertEqual(len(self.client.get('/api/transactions').json['transactions']), 5)
        self.assertEqual(self.client.get('/api/financial-health').json['score'], 78)
        self.assertFalse(self.client.post('/api/auth/demo').json['authenticated'])

    def test_missing_database_is_clear_and_nonfatal(self):
        self.assertEqual(self.client.get('/api/health/database').status_code, 503)
        with self.app.app_context(), self.assertRaises(DatabaseUnavailable):
            get_collection('users')
        self.assertEqual(self.client.get('/api/dashboard').status_code, 200)

    def test_invalid_uri_does_not_crash(self):
        app = create_app({'TESTING': True, 'MONGO_URI': 'invalid://host'})
        self.assertEqual(app.test_client().get('/api/health').status_code, 200)

    def test_cors_allowlist(self):
        allowed = self.client.get('/api/health', headers={'Origin': 'http://localhost:5173'})
        denied = self.client.get('/api/health', headers={'Origin': 'https://untrusted.example'})
        self.assertEqual(allowed.headers['Access-Control-Allow-Origin'], 'http://localhost:5173')
        self.assertNotIn('Access-Control-Allow-Origin', denied.headers)

    def test_errors_are_json(self):
        response = self.client.get('/api/does-not-exist')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json)

if __name__ == '__main__':
    unittest.main()

