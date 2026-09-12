"""Explicit UI QA server. In-memory fixtures only; never opens an Atlas connection."""
import sys
import os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datetime import date
import mongomock
from app import create_app
from services.synthetic import generate
from seed_demo_users import seed_demo_users

qa_origins = [origin.strip() for origin in os.getenv('QA_CORS_ORIGINS', 'http://127.0.0.1:5174').split(',') if origin.strip()]
app=create_app({'MONGO_URI':'','CORS_ORIGINS':qa_origins})
app.extensions['mongo']=mongomock.MongoClient()
for name,rows in generate(date(2026,9,12)).items():
    app.extensions['mongo']['paisaSaathiDB'][name].insert_many(rows)
with app.app_context():
    seed_demo_users()

@app.after_request
def label_fixture(response):
    payload=response.get_json(silent=True)
    if isinstance(payload,dict) and 'source' in payload:
        payload['source']='test-fixture'
        response.set_data(app.json.dumps(payload))
    return response

if __name__=='__main__':
    print('UI QA fixture server: no Atlas connection or persistence.',flush=True)
    app.run(host='127.0.0.1',port=int(os.getenv('QA_PORT', '5001')),debug=False)
