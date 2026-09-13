from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from services.auth import current_identity
from services.chat_assistant import answer


bp = Blueprint('chat', __name__)


@bp.post('/chat')
def chat():
    customer_id = current_identity(required=True)
    data = request.get_json(silent=True)
    if not isinstance(data, dict): raise BadRequest('Send a JSON object.')
    message = data.get('message')
    if not isinstance(message, str) or not message.strip(): raise BadRequest('Message is required.')
    if len(message.strip()) > 2000: raise BadRequest('Message must be 2,000 characters or fewer.')
    history = data.get('conversation_context', [])
    if not isinstance(history, list): raise BadRequest('Conversation context must be a list.')
    clean_history = []
    for item in history[-8:]:
        if not isinstance(item, dict) or item.get('role') not in {'user', 'assistant'} or not isinstance(item.get('content'), str):
            raise BadRequest('Conversation context contains an invalid message.')
        clean_history.append({'role': item['role'], 'content': item['content'][:1000]})
    return jsonify(answer(customer_id, message.strip(), clean_history))
