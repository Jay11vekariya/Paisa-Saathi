import json
from pathlib import Path

# Shared fixture is used by the API and the frontend's explicitly labeled fallback.
DEMO = json.loads((Path(__file__).resolve().parents[2] / 'data' / 'demo.json').read_text(encoding='utf-8'))
