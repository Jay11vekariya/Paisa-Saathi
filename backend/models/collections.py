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
    current_app.logger.info('Prepared the seven Phase 1 collections without inserting data.')
