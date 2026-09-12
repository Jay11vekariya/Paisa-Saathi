from flask import Blueprint, jsonify
from services.demo import DEMO

bp = Blueprint('dashboard', __name__)

@bp.get('/dashboard')
def dashboard():
    return jsonify(DEMO['dashboard'])

@bp.get('/financial-health')
def financial_health():
    return jsonify(**DEMO['dashboard']['health'], source='demo')

