from flask import current_app
from pymongo import MongoClient
from pymongo.errors import PyMongoError

COLLECTIONS = ('users', 'transactions', 'financial_profiles', 'recommendations', 'alerts', 'chat_history', 'products')

class DatabaseUnavailable(Exception):
    pass

def init_db(app):
    app.extensions['mongo'] = None
    uri = app.config['MONGO_URI']
    if not uri:
        app.logger.warning('MongoDB is not configured. Set MONGO_URI in backend/.env; demo endpoints remain available.')
        return
    client = None
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=8000, connectTimeoutMS=6000, socketTimeoutMS=30000)
        app.extensions['mongo'] = client
        client.admin.command('ping')
        app.logger.info('MongoDB connected to database %s', app.config['MONGO_DB_NAME'])
    except (PyMongoError, ValueError):
        # Retain a valid client so the driver can recover after a temporary outage.
        # Invalid URI construction still leaves the extension unset.
        app.logger.error('MongoDB is unavailable. Check URI, Atlas network access, and database user permissions. Configured clients retry on the next request.')

def get_collection(name):
    if name not in COLLECTIONS:
        raise ValueError('Unknown collection')
    client = current_app.extensions.get('mongo')
    if client is None:
        raise DatabaseUnavailable('MongoDB is unavailable. Check the server database configuration.')
    return client[current_app.config['MONGO_DB_NAME']][name]

def database_status():
    client = current_app.extensions.get('mongo')
    if client is None:
        return 'unavailable'
    try:
        client.admin.command('ping')
        return 'connected'
    except PyMongoError:
        return 'unavailable'


