import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'))

class Config:
    MONGO_URI = os.getenv('MONGO_URI', '')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'paisaSaathiDB')
    CORS_ORIGINS = [x.strip() for x in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if x.strip()]
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'development-only-change-me-please-set-a-unique-secret')
    JWT_EXPIRY_HOURS = int(os.getenv('JWT_EXPIRY_HOURS', '24'))
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'ollama')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434').rstrip('/')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:1.7b')
    OLLAMA_TIMEOUT_SECONDS = int(os.getenv('OLLAMA_TIMEOUT_SECONDS', '150'))
    OLLAMA_CONTEXT_SIZE = int(os.getenv('OLLAMA_CONTEXT_SIZE', '4096'))
    OLLAMA_MAX_TOKENS = int(os.getenv('OLLAMA_MAX_TOKENS', '250'))
