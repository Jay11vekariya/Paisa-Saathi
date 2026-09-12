from flask import current_app
from pymongo.errors import CollectionInvalid
from db import COLLECTIONS, get_collection

def prepare_collections():
    # Explicit command: do not create or seed collections during read-only API startup.
    database = get_collection('users').database
    existing = set(database.list_collection_names())
    for name in COLLECTIONS:
        if name not in existing:
            try:
                database.create_collection(name)
            except CollectionInvalid:
                pass  # Another process may have created it concurrently.
    users = database['users']
    users.create_index('email', unique=True, sparse=True)
    users.create_index('customer_id', unique=True)
    database['customer_profiles'].create_index('customer_id', unique=True)
    database['transactions'].create_index([('customer_id', 1), ('date', -1)])
    current_app.logger.info('Prepared application collections and indexes without inserting data.')
