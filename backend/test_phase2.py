"""Unit and mock-database integration tests. No Atlas network access."""
import copy
import math
import unittest
from datetime import date
from unittest.mock import patch, MagicMock
import mongomock
from mongomock.collection import BulkOperationBuilder
from pymongo.errors import ServerSelectionTimeoutError
from werkzeug.exceptions import BadRequest
from app import create_app
from seed import seed_data
from services.synthetic import generate, DATASET, completed_months
from services.financial_health import analyse, change, months_between
from services.financial_state import determine_state
from services.recommendations import recommend
from utils.validation import validate_transaction

# mongomock 4.3 predates PyMongo's optional sort argument on ReplaceOne.
_original_replace = BulkOperationBuilder.add_replace

def compatible_replace(self, selector, doc, upsert, collation=None, hint=None, sort=None):
    if sort is not None:
        raise AssertionError('This test adapter does not emulate sorted replacements.')
    return _original_replace(self, selector, doc, upsert, collation=collation, hint=hint)

DATA = generate(date(2026, 9, 12))

def analysis(number=0):
    user=DATA['users'][number]
    return analyse(user,[t for t in DATA['transactions'] if t['customer_id']==user['customer_id']],DATA['financial_profiles'][number])

class AnalyticsTests(unittest.TestCase):
    def test_reproducible_dataset_and_completed_months(self):
        self.assertEqual(DATA,generate(date(2026,9,12)))
        self.assertEqual(completed_months(date(2026,1,3))[-1],'2025-12')
        self.assertEqual(len(DATA['users']),20)
        self.assertEqual(len({t['transaction_id'] for t in DATA['transactions']}),len(DATA['transactions']))
        self.assertEqual({t['date'][:7] for t in DATA['transactions']},set(months_between('2025-12','2026-08')))
        for t in DATA['transactions']:
            validate_transaction(t)
            self.assertLess(date.fromisoformat(t['date']),date(2026,9,1))

    def test_four_scenarios_are_calculated(self):
        self.assertEqual([analysis(i)['financial_state']['state'] for i in range(4)],['GROWTH','NORMAL','CAUTION','SUPPORT'])
        self.assertGreater(analysis(0)['financial_health']['score'],analysis(2)['financial_health']['score'])
        self.assertTrue(analysis(3)['metrics']['emi_payment_gap'])
        self.assertTrue(analysis(3)['metrics']['income_disruption'])

    def test_cashflow_and_score_reconcile_for_every_customer(self):
        for i,user in enumerate(DATA['users']):
            result=analysis(i); m=result['metrics']; h=result['financial_health']
            with self.subTest(customer=user['customer_id']):
                self.assertAlmostEqual(m['monthly_income']-m['monthly_expenses'],m['monthly_savings'],places=2)
                self.assertAlmostEqual(sum(c['amount'] for c in result['spending']['categories']),m['monthly_expenses'],places=2)
                self.assertAlmostEqual(sum(d['amount'] for d in result['spending']['daily']),m['monthly_expenses'],places=2)
                self.assertAlmostEqual(m['account_balance'],user['account_balance'],places=2)
                self.assertEqual(sum(f['weight'] for f in h['factors']),100)
                self.assertEqual(h['score'],math.floor(sum(f['contribution'] for f in h['factors'])+.5))
                self.assertTrue(0<=h['score']<=100)
                self.assertTrue(all(t['customer_id']==user['customer_id'] for t in result['recent_transactions']))
                self.assertNotIn('credit score',h['status'].lower())

    def test_changed_ledger_changes_results(self):
        user=DATA['users'][0]; rows=copy.deepcopy([t for t in DATA['transactions'] if t['customer_id']==user['customer_id']])
        for row in rows:
            if row['date'].startswith('2026-08') and row['type']=='credit': row['amount']=1000
        result=analyse(user,rows,DATA['financial_profiles'][0])
        self.assertEqual(result['metrics']['monthly_income'],1000)
        self.assertEqual(result['financial_state']['state'],'SUPPORT')
        self.assertLess(result['financial_health']['score'],analysis()['financial_health']['score'])

    def test_missing_income_month_counts_as_zero(self):
        user=DATA['users'][0]
        rows=[t for t in DATA['transactions'] if t['customer_id']==user['customer_id'] and not (t['date'].startswith('2026-08') and t['type']=='credit')]
        result=analyse(user,rows,DATA['financial_profiles'][0])
        self.assertEqual(result['metrics']['monthly_income'],0)
        self.assertEqual(result['financial_health']['factors'][0]['contribution'],0)
        self.assertEqual(result['financial_state']['state'],'SUPPORT')
        self.assertTrue(all(math.isfinite(v) for v in result['metrics'].values() if isinstance(v,(int,float))))
        self.assertIsNone(change(500,0)); self.assertIsNone(change(100,-500))

    def test_configured_client_recovers_after_startup_outage(self):
        client=MagicMock()
        client.admin.command.side_effect=[ServerSelectionTimeoutError('temporary'), {'ok':1}]
        with patch('db.MongoClient',return_value=client):
            app=create_app({'TESTING':True,'MONGO_URI':'mongodb://test.invalid'})
        self.assertIs(app.extensions['mongo'],client)
        self.assertEqual(app.test_client().get('/api/health/database').status_code,200)
        client.close.assert_not_called()

    def test_state_precedence_and_thresholds(self):
        m=analysis()['metrics']
        m={**m,'emi_burden':36,'emi_payment_gap':False,'income_disruption':False}
        self.assertEqual(determine_state(m)['state'],'CAUTION')
        m['income_disruption']=True
        self.assertEqual(determine_state(m)['state'],'SUPPORT')

    def test_recommendations_are_explainable_and_state_aware(self):
        for number, expected in enumerate(['GROWTH','NORMAL','CAUTION','SUPPORT']):
            result=analysis(number)
            recommendations= recommend(result['metrics'],result['financial_state'],DATA['products'])
            with self.subTest(state=expected):
                self.assertEqual(recommendations['financial_state'],expected)
                self.assertTrue(recommendations['recommendations'])
                self.assertTrue(all(row['action'] and row['category'] and row['reason'] and row['why_this'] and row['why_it_may_help'] and row['suitability'] and row['confidence'] and row['priority'] for row in recommendations['recommendations']))
                self.assertTrue(all(row['why_not_this'] and row['rejection_conditions'] and row['safer_alternative']['action'] for row in recommendations['not_recommended']))
                self.assertEqual(recommendations['engine']['decision_mode'],'deterministic')
        support=recommend(analysis(3)['metrics'],analysis(3)['financial_state'],DATA['products'])
        self.assertEqual(support['recommendations'][0]['product']['product_id'],'PR007')
        self.assertIn('PR005',{row['product']['product_id'] for row in support['not_recommended']})
        self.assertNotIn('PR005',{row['product']['product_id'] for row in support['recommendations']})

    def test_healthy_customer_gets_suitable_savings_and_no_default_loan(self):
        result=recommend(analysis(0)['metrics'],analysis(0)['financial_state'],DATA['products'])
        product_ids={row['product']['product_id'] for row in result['recommendations']}
        rejected={row['product']['product_id']:row for row in result['not_recommended']}
        self.assertIn('PR002',product_ids)
        self.assertIn('PR005',rejected)
        self.assertIn('no stated borrowing need',rejected['PR005']['why_not_this'])

    def test_stressed_customer_rejection_names_conditions_and_safe_alternative(self):
        result=recommend(analysis(3)['metrics'],analysis(3)['financial_state'],DATA['products'])
        rejected={row['product']['product_id']:row for row in result['not_recommended']}
        loan=rejected['PR005']
        self.assertTrue(any('income' in condition.lower() or 'emi' in condition.lower() for condition in loan['rejection_conditions']))
        self.assertEqual(loan['safer_alternative']['category'],'Financial guidance')
        self.assertIn('repayment',loan['safer_alternative']['action'].lower())

    def test_malformed_transactions_are_rejected(self):
        row=DATA['transactions'][0]
        for field,values in {'amount':[0,-1,float('nan'),float('inf'),True,'20'],'type':['refund',''],'date':['2026-02-30','2026-8-1','bad'],'category':['Unknown'],'customer_id':['$ne','../../x','PS01']}.items():
            for value in values:
                with self.subTest(field=field,value=value), self.assertRaises((ValueError,BadRequest)):
                    validate_transaction({**row,field:value})

class MongoIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app=create_app({'TESTING':True,'MONGO_URI':''})
        self.mongo=mongomock.MongoClient()
        self.app.extensions['mongo']=self.mongo
        self.client=self.app.test_client()
        for name,rows in DATA.items():
            self.mongo.paisaSaathiDB[name].insert_many(copy.deepcopy(rows))

    def test_all_customer_endpoints(self):
        self.assertEqual(len(self.client.get('/api/customers').json['customers']),20)
        for endpoint in ['dashboard','transactions','financial-health','financial-state','spending','recommendations']:
            with self.subTest(endpoint=endpoint):
                response=self.client.get('/api/'+endpoint+'/PS001')
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.json['source'],'mongodb')
                self.assertNotIn('MONGO_URI',response.get_data(as_text=True))
        self.assertEqual(self.client.get('/api/dashboard/PS003').json['financial_state']['state'],'CAUTION')

    def test_recommendation_api_uses_calculated_customer_state(self):
        support=self.client.get('/api/recommendations/PS004')
        self.assertEqual(support.status_code,200)
        self.assertEqual(support.json['financial_state'],'SUPPORT')
        self.assertEqual(support.json['recommendations'][0]['product']['product_id'],'PR007')
        self.assertTrue(support.json['not_recommended'])
        self.assertIn('safer_alternative',support.json['not_recommended'][0])
        self.assertIn('confidence',support.json['recommendations'][0])
        self.assertEqual(self.client.get('/api/recommendations/bad').status_code,400)

    def test_customer_isolation_and_pagination(self):
        first=self.client.get('/api/transactions/PS002?page=1&limit=20').json
        second=self.client.get('/api/transactions/PS002?page=2&limit=20').json
        self.assertEqual(len(first['transactions']),20)
        self.assertTrue(all(t['customer_id']=='PS002' for t in first['transactions']+second['transactions']))
        self.assertFalse({t['transaction_id'] for t in first['transactions']} & {t['transaction_id'] for t in second['transactions']})
        self.assertEqual(first['total'],sum(t['customer_id']=='PS002' for t in DATA['transactions']))
        for url in ['/api/dashboard/bad','/api/transactions/PS001?page=0','/api/transactions/PS001?limit=101','/api/transactions/PS001?page=abc']:
            self.assertEqual(self.client.get(url).status_code,400)
        self.assertEqual(self.client.get('/api/dashboard/PS999').status_code,404)

    def test_non_synthetic_users_never_exposed(self):
        self.mongo.paisaSaathiDB.users.insert_one({'customer_id':'PS999','name':'Private record','synthetic':False})
        self.assertEqual(self.client.get('/api/dashboard/PS999').status_code,404)
        self.assertEqual(len(self.client.get('/api/customers').json['customers']),20)

    def test_incomplete_history_and_database_outage(self):
        self.mongo.paisaSaathiDB.financial_profiles.delete_one({'customer_id':'PS001'})
        self.assertEqual(self.client.get('/api/dashboard/PS001').status_code,409)
        with patch('services.customer_data.get_collection',side_effect=ServerSelectionTimeoutError('test outage')):
            response=self.client.get('/api/dashboard/PS001')
            self.assertEqual(response.status_code,503)
            self.assertNotIn('test outage',response.get_data(as_text=True))

    def test_seed_is_idempotent_and_preserves_other_data(self):
        self.mongo=mongomock.MongoClient()
        self.app.extensions['mongo']=self.mongo
        self.mongo.EmployeeDB.employees.insert_one({'sentinel':'untouched'})
        self.mongo.paisaSaathiDB.alerts.insert_one({'sentinel':'untouched'})
        sample={k:copy.deepcopy(v[:2] if k!='transactions' else v[:40]) for k,v in DATA.items()}
        with self.app.app_context(),patch.object(BulkOperationBuilder,'add_replace',compatible_replace):
            first=seed_data(sample)
            second=seed_data(sample)
        self.assertEqual(first,second)
        self.assertEqual(first['transactions'],40)
        self.assertEqual(first['users'],2)
        self.assertEqual(first['products'],2)
        self.assertEqual(self.mongo.EmployeeDB.employees.count_documents({}),1)
        self.assertEqual(self.mongo.paisaSaathiDB.alerts.count_documents({}),1)

    def test_seed_rejects_other_database_and_id_collisions(self):
        self.app.config['MONGO_DB_NAME']='EmployeeDB'
        with self.app.app_context(),self.assertRaises(ValueError): seed_data(DATA)
        self.assertEqual(self.mongo.EmployeeDB.users.count_documents({}),0)
        self.app.config['MONGO_DB_NAME']='paisaSaathiDB'
        self.mongo.paisaSaathiDB.users.update_one({'customer_id':'PS001'},{'$set':{'synthetic':False}})
        with self.app.app_context(),self.assertRaises(ValueError): seed_data(DATA)
        self.assertFalse(self.mongo.paisaSaathiDB.users.find_one({'customer_id':'PS001'})['synthetic'])

if __name__=='__main__':
    unittest.main()

