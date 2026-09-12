import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'))

class Config:
    MONGO_URI = os.getenv('MONGO_URI', '')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'paisaSaathiDB')
    CORS_ORIGINS = [x.strip() for x in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]
