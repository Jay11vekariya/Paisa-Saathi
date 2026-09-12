from flask import Blueprint, jsonify
from db import database_status

bp = Blueprint('health', __name__)

@bp.get('/health')
def health():
    return jsonify(status='ok', service='Paisa Saathi API', version='1.0.0')

@bp.get('/health/database')
def database_health():
    status = database_status()
    return jsonify(status=status, database='paisaSaathiDB'), 200 if status == 'connected' else 503
