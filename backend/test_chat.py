"""Focused tests for the grounded vernacular banking assistant."""
import copy
import json
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

import mongomock

from app import create_app
from seed_demo_users import demo_email, demo_password, seed_demo_users
from services.chat_assistant import (OllamaProviderError, _call_ollama,
                                     _extract_loan_details, _response_quality_issue,
                                     detect_financial_concept, detect_intent, detect_language)
from services.synthetic import generate


class ChatApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True, 'MONGO_URI': '', 'AI_PROVIDER': 'ollama',
                               'OLLAMA_BASE_URL':'http://127.0.0.1:11434',
                               'JWT_SECRET_KEY': 'test-secret-at-least-thirty-two-bytes'})
        self.app.extensions['mongo'] = mongomock.MongoClient()
        data = generate(date(2026, 9, 12))
        for name, rows in data.items():
            self.app.extensions['mongo'].paisaSaathiDB[name].insert_many(copy.deepcopy(rows))
        with self.app.app_context(): seed_demo_users()
        self.client = self.app.test_client()
        self.ollama_patch = patch('services.chat_assistant._call_ollama',
                                  side_effect=OllamaProviderError('service_unavailable'))
        self.ollama_patch.start()
        self.addCleanup(self.ollama_patch.stop)

    def login(self, customer_id='PS001'):
        response = self.client.post('/api/auth/login', json={
            'email': demo_email(customer_id), 'password': demo_password(customer_id)})
        return {'Authorization': f"Bearer {response.json['token']}"}

    def test_chat_requires_auth_and_valid_message(self):
        self.assertEqual(self.client.post('/api/chat', json={'message':'Hello'}).status_code, 401)
        headers = self.login()
        self.assertEqual(self.client.post('/api/chat', headers=headers, json={}).status_code, 400)
        self.assertEqual(self.client.post('/api/chat', headers=headers, json={'message':'  '}).status_code, 400)
        self.assertEqual(self.client.post('/api/chat', headers=headers,
                                          json={'message':'Hello', 'conversation_context':'invalid'}).status_code, 400)

    def test_language_detection(self):
        self.assertEqual(detect_language('How is my financial health?'), 'English')
        self.assertEqual(detect_language('મારી financial health કેવી છે?'), 'Gujarati-mixed')
        self.assertEqual(detect_language('मेरा financial stress ज्यादा क्यों है?'), 'Hindi-mixed')
        self.assertEqual(detect_language('mare loan levi che su karu'), 'Gujarati-mixed')
        self.assertEqual(detect_language('mera EMI kitna hoga'), 'Hindi-mixed')
        self.assertEqual(detect_language('mujhe loan lena hai'), 'Hindi-mixed')
        self.assertEqual(detect_language('मेरी financial health कैसी है?'), 'Hindi-mixed')
        headers = self.login()
        response = self.client.post('/api/chat', headers=headers, json={'message':'મારી financial health કેવી છે?'})
        self.assertEqual(response.json['detected_language'], 'Gujarati-mixed')
        self.assertTrue(any('\u0A80' <= character <= '\u0AFF' for character in response.json['assistant_message']))

    def test_product_intents_are_explicit_and_do_not_depend_on_llm(self):
        cases = {
            'Hello!':'greeting', 'How is my financial health?':'health',
            'Why is my stress high?':'stress', 'Where do I spend most?':'spending',
            'How much am I saving?':'savings', 'What do you recommend?':'recommendations',
            'Why are you recommending this?':'why_recommendation', "Why shouldn't I take it?":'why_not',
            'I want a loan':'loan', 'Why was this flagged as fraud?':'anomaly',
            'Show my alerts':'alerts', 'Help with KYC':'kyc',
            'Set up my account':'onboarding', 'How is my data used?':'privacy',
        }
        for message, expected in cases.items():
            with self.subTest(message=message): self.assertEqual(detect_intent(message), expected)

    def test_verified_context_is_grounded_and_customer_isolated(self):
        captured = {}
        def fake_call(message, language, history, context):
            captured.update(context)
            return 'Grounded answer.'
        with patch('services.chat_assistant._call_ollama', side_effect=fake_call):
            response = self.client.post('/api/chat?customer_id=PS003', headers=self.login('PS001'),
                                        json={'message':'How is my financial health?'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['provider'], 'Ollama')
        self.assertFalse(response.json['fallback'])
        self.assertEqual(response.json['grounded_context']['customer_id'], 'PS001')
        self.assertIsInstance(captured['financial_snapshot']['health_score'], int)
        self.assertNotIn('password_hash', str(captured))

    def test_insufficient_data_user_receives_grounded_boundary(self):
        registered = self.client.post('/api/auth/register', json={
            'full_name':'New User', 'email':'chat-new@example.test', 'password':'secure-pass-1',
            'confirm_password':'secure-pass-1'})
        headers = {'Authorization': f"Bearer {registered.json['token']}"}
        response = self.client.post('/api/chat', headers=headers, json={'message':'How is my financial health?'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json['grounded_context']['personalized'])
        self.assertIn('completed profile', response.json['assistant_message'])

    def test_ai_failure_uses_safe_grounded_fallback(self):
        with patch('services.chat_assistant._call_ollama', side_effect=OllamaProviderError('service_unavailable')):
            response = self.client.post('/api/chat', headers=self.login('PS003'),
                                        json={'message':'Why is my financial stress high?'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['fallback'])
        self.assertIn('66/100', response.json['assistant_message'])
        self.assertEqual(response.json['grounded_context']['customer_id'], 'PS003')

    def test_open_ended_general_question_uses_local_llm_without_customer_engines(self):
        with patch('services.chat_assistant.dashboard_for_authenticated') as dashboard, \
             patch('services.chat_assistant._call_ollama', return_value='EMI is a fixed monthly loan payment.'):
            response = self.client.post('/api/chat', headers=self.login('PS001'),
                                        json={'message':'What is EMI?'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['assistant_message'], 'EMI is a fixed monthly loan payment.')
        self.assertFalse(response.json['fallback'])
        dashboard.assert_not_called()

    def test_model_unavailable_uses_offline_safe_fallback(self):
        with patch('services.chat_assistant._call_ollama',
                   side_effect=OllamaProviderError('model_unavailable')):
            response = self.client.post('/api/chat', headers=self.login('PS001'),
                                        json={'message':'Explain compound interest.'})
        self.assertTrue(response.json['fallback'])
        self.assertIn('Compound interest', response.json['assistant_message'])
        self.assertIn('verified_financial_concepts', response.json['grounded_context']['sources'])

    def test_ollama_timeout_returns_friendly_fallback(self):
        with patch('services.chat_assistant._call_ollama',
                   side_effect=OllamaProviderError('timeout')):
            response = self.client.post('/api/chat', headers=self.login('PS001'),
                                        json={'message':'Explain compound interest.'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['fallback'])
        self.assertIn('Compound interest', response.json['assistant_message'])
        self.assertNotIn('timed out', response.json['assistant_message'].lower())

    def test_small_verified_concept_layer_is_natural_and_multilingual(self):
        cases = [
            ('What is compound interest?', 'compound_interest', 'English', 'original principal'),
            ('EMI શું છે? મને સરળ ભાષામાં સમજાવો.', 'emi', 'Gujarati-mixed', 'સમાન માસિક હપ્તો'),
            ('EMI क्या है? आसान भाषा में समझाओ।', 'emi', 'Hindi-mixed', 'समान मासिक किस्त'),
        ]
        headers = self.login()
        for message, concept, language, expected in cases:
            with self.subTest(message=message):
                self.assertEqual(detect_financial_concept(message), concept)
                response = self.client.post('/api/chat', headers=headers, json={'message':message})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json['detected_language'], language)
                self.assertIn(expected, response.json['assistant_message'])
                self.assertIn('verified_financial_concepts', response.json['grounded_context']['sources'])

    def test_requested_multilingual_health_and_loan_prompts(self):
        headers = self.login()
        cases = [
            ('મારી financial health કેવી છે?', 'Gujarati-mixed', 'health', 'તમારી ચકાસેલી'),
            ('मेरी financial health कैसी है?', 'Hindi-mixed', 'health', 'आपकी सत्यापित'),
            ('mare loan levi che', 'Gujarati-mixed', 'loan', 'જણાવશો'),
            ('mujhe loan lena hai', 'Hindi-mixed', 'loan', 'बताइए'),
        ]
        for message, language, intent, expected in cases:
            with self.subTest(message=message):
                response = self.client.post('/api/chat', headers=headers, json={'message':message})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json['detected_language'], language)
                self.assertEqual(response.json['intent'], intent)
                self.assertIn(expected, response.json['assistant_message'])
                self.assertTrue(response.json['intent_code'])
                self.assertTrue(response.json['actions'])

    def test_multilingual_quality_gate_rejects_corruption(self):
        context = {'financial_concept': {
            'name':'emi',
            'localized_reference':'EMI (સમાન માસિક હપ્તો) એટલે લોન ચૂકવવા માટે દર મહિને ભરવાની નક્કી રકમ.',
        }}
        self.assertEqual(_response_quality_issue(
            'EMI એ કારોબાંબાં પર પેન્સિયન કરવાનો વિતરણ છે.', 'Gujarati-mixed', context),
            'malformed_word')
        self.assertIsNone(_response_quality_issue(
            'EMI એટલે લોન ચૂકવવા માટે દર મહિને ભરવાનો સમાન માસિક હપ્તો.',
            'Gujarati-mixed', context))
        hindi_context = {'financial_concept': {
            'name':'emi',
            'localized_reference':'EMI (समान मासिक किस्त) लोन चुकाने के लिए हर महीने दी जाने वाली तय रकम है।',
        }}
        repeated = ('EMI समान मासिक किस्त है। लोन के अंतराल के अनुसार तय किया जाता है और '
                    'लोन के अंतराल के अनुसार तय किया जाता है।')
        self.assertEqual(_response_quality_issue(repeated, 'Hindi-mixed', hindi_context),
                         'repeated_text')
        personalized = {
            'personalized': True,
            'localized_reference': ('તમારી ચકાસેલી financial health Strong છે અને score 94/100 છે. '
                                    'માસિક surplus ₹32,551 છે.'),
        }
        corrupted = ('મારી ફિનાન્સિયલ હેલ્થ સ્ટોરેજ સ્કોર 94 છે, જે સ્ટોરેજ સ્ટેટસ '
                     'સ્ટોરેજ ઓફિસ છે અને સ્થિતિ ગ્રોટાન છે.')
        self.assertEqual(_response_quality_issue(corrupted, 'Gujarati-mixed', personalized),
                         'ungrounded_language')

    def test_ollama_local_http_client_success_and_external_url_rejected(self):
        tags_response = MagicMock()
        tags_response.__enter__.return_value.read.return_value = json.dumps({
            'models': [{'name':'qwen3:1.7b'}]}).encode()
        chat_response = MagicMock()
        chat_response.__enter__.return_value.read.return_value = json.dumps({
            'message': {'role':'assistant', 'content':'Local answer'}}).encode()
        with self.app.app_context(), patch('services.chat_assistant.urlrequest.urlopen',
                                            side_effect=[tags_response, chat_response]) as urlopen:
            self.assertEqual(_call_ollama('Explain EMI', 'English', [], {
                'mode':'general_financial_education'}), 'Local answer')
            self.assertEqual(urlopen.call_args_list[0].args[0], 'http://127.0.0.1:11434/api/tags')
            self.assertTrue(urlopen.call_args_list[1].args[0].full_url.startswith('http://127.0.0.1:11434/'))

            self.app.config['OLLAMA_BASE_URL'] = 'https://external.example'
            with self.assertRaises(OllamaProviderError):
                _call_ollama('Hello', 'English', [], {})
            self.assertEqual(urlopen.call_count, 2)

    def test_loan_value_extraction_variants(self):
        self.assertEqual(_extract_loan_details('ammount 2L')['loan_amount'], 200000)
        details = _extract_loan_details('₹2 lakh, intreset 8%, tennure 1 year')
        self.assertEqual(details['loan_amount'], 200000)
        self.assertEqual(details['annual_interest_rate'], 8)
        self.assertEqual(details['tenure_months'], 12)

    def test_loan_follow_up_collects_details_and_uses_real_simulator(self):
        headers = self.login('PS001')
        history = [
            {'role':'user', 'content':'mare loan levi che su karu'},
            {'role':'assistant', 'content':'લોન amount, interest rate અને tenure જણાવો.'},
        ]
        response = self.client.post('/api/chat', headers=headers, json={
            'message':'amount = 200000, intreset = 8%, tennure = 1 year',
            'conversation_context': history,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['intent'], 'loan')
        self.assertEqual(response.json['detected_language'], 'Gujarati-mixed')
        self.assertIn('loan_simulator', response.json['grounded_context']['sources'])
        self.assertIn('EMI', response.json['assistant_message'])
        self.assertIn('₹200,000', response.json['assistant_message'])

    def test_loan_details_accumulate_across_turns_and_why_stays_in_context(self):
        headers = self.login('PS001')
        history = [{'role':'user', 'content':'I want a loan'}]
        amount = self.client.post('/api/chat', headers=headers, json={
            'message':'2 lakh', 'conversation_context': history}).json
        self.assertIn('annual interest rate', amount['assistant_message'])
        self.assertIn('tenure', amount['assistant_message'])

        history.extend([
            {'role':'user', 'content':'2 lakh'},
            {'role':'assistant', 'content':amount['assistant_message']},
        ])
        rate = self.client.post('/api/chat', headers=headers, json={
            'message':'8%', 'conversation_context':history}).json
        self.assertNotIn('loan amount and', rate['assistant_message'])
        self.assertIn('tenure', rate['assistant_message'])

        history.extend([
            {'role':'user', 'content':'8%'},
            {'role':'assistant', 'content':rate['assistant_message']},
        ])
        result = self.client.post('/api/chat', headers=headers, json={
            'message':'1 year', 'conversation_context':history}).json
        self.assertIn('loan_simulator', result['grounded_context']['sources'])
        self.assertEqual(result['detected_language'], 'English')

        why_history = history + [
            {'role':'user', 'content':'1 year'},
            {'role':'assistant', 'content':result['assistant_message']},
        ]
        why = self.client.post('/api/chat', headers=headers, json={
            'message':'why?', 'conversation_context':why_history}).json
        self.assertEqual(why['intent'], 'loan')
        self.assertIn('loan_simulator', why['grounded_context']['sources'])

    def test_anomaly_context_and_persisted_history_are_customer_isolated(self):
        first = self.client.post('/api/chat', headers=self.login('PS001'),
                                 json={'message':'Explain my unusual transaction alert'})
        second = self.client.post('/api/chat', headers=self.login('PS003'),
                                  json={'message':'How is my financial health?'})
        self.assertIn('anomaly_detection', first.json['grounded_context']['sources'])
        collection = self.app.extensions['mongo'].paisaSaathiDB.chat_history
        self.assertEqual(collection.count_documents({'customer_id':'PS001'}), 2)
        self.assertEqual(collection.count_documents({'customer_id':'PS003'}), 2)
        self.assertNotEqual(first.json['grounded_context']['customer_id'],
                            second.json['grounded_context']['customer_id'])


if __name__ == '__main__': unittest.main()
