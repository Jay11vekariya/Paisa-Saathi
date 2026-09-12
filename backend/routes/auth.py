from flask import Blueprint, jsonify
from services.auth import demo_identity

bp = Blueprint('auth', __name__)

@bp.post('/auth/demo')
def demo():
    return jsonify(demo_identity())
