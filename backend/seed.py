"""Run explicitly. Upserts synthetic records; never drops databases or collections."""
import argparse
from datetime import date
from pymongo import ReplaceOne
from pymongo.errors import PyMongoError
from app import create_app
from db import get_collection, DatabaseUnavailable
from models.collections import prepare_collections
from services.synthetic import generate, write_csv, DATASET

KEYS = {'users':'customer_id','transactions':'transaction_id','financial_profiles':'customer_id','products':'product_id'}

def seed_data(data):
    from flask import current_app
    if current_app.config['MONGO_DB_NAME'] != 'paisaSaathiDB':
        raise ValueError('Seed is restricted to paisaSaathiDB.')
    # Validate the entire batch before making any database changes.
    from utils.validation import validate_transaction
    for row in data['transactions']:
        validate_transaction(row)
    # Do not overwrite non-synthetic records with colliding IDs.
    for name,key in KEYS.items():
        ids = [row[key] for row in data[name]]
        collision = get_collection(name).find_one({key:{'$in':ids},'$or':[{'synthetic':{'$ne':True}},{'dataset':{'$ne':DATASET}}]},{'_id':1})
        if collision:
            raise ValueError('Seed IDs conflict with records outside this synthetic dataset.')
    prepare_collections()
    for name,key in KEYS.items():
        collection = get_collection(name)
        collection.create_index(key,unique=True)
        rows = data[name]
        for offset in range(0,len(rows),200):
            collection.bulk_write([ReplaceOne({key:row[key],'synthetic':True,'dataset':DATASET},row,upsert=True) for row in rows[offset:offset+200]],ordered=True)
        print(f'Prepared {name}: {len(rows)} synthetic records.',flush=True)
    get_collection('transactions').create_index([('customer_id',1),('date',-1),('transaction_id',-1)])
    return {name:get_collection(name).count_documents({'dataset':DATASET,'synthetic':True}) for name in KEYS}

def main():
    parser = argparse.ArgumentParser(description='Upsert fictional Phase 2 data into paisaSaathiDB. No clearing or deletion is performed.')
    parser.add_argument('--as-of',type=date.fromisoformat,default=date.today(),help='Generate the preceding nine completed months (YYYY-MM-DD).')
    parser.add_argument('--csv-only',action='store_true',help='Generate CSVs without accessing MongoDB.')
    args = parser.parse_args()
    data = generate(args.as_of)
    write_csv(data)
    if args.csv_only:
        print('Synthetic CSVs generated; no database accessed.')
        return 0
    app = create_app()
    try:
        with app.app_context():
            counts = seed_data(data)
        print('Seed complete in paisaSaathiDB:',counts)
        return 0
    except (DatabaseUnavailable,PyMongoError,ValueError):
        print('Seed failed. Check Atlas connectivity, permissions, or conflicting record IDs. No other database was accessed.')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())

