from werkzeug.exceptions import NotFound, Conflict
from db import get_collection
from utils.validation import customer_id
from services.financial_health import analyse
from services.recommendations import recommend
from services.segmentation import segment_customer

USER_FIELDS = {'_id':0,'dataset':0}
TX_FIELDS = {'_id':0,'dataset':0,'synthetic':0}

def list_customers():
    return list(get_collection('users').find({'synthetic':True},{'_id':0,'customer_id':1,'name':1,'city':1,'language':1}).sort('customer_id',1))

def load_customer(cid):
    customer_id(cid)
    user = get_collection('users').find_one({'customer_id':cid,'synthetic':True},dict(USER_FIELDS))
    if user is None:
        raise NotFound('Synthetic customer not found.')
    return user

def is_synthetic_customer(cid):
    return get_collection('users').find_one({'customer_id':cid, 'synthetic':True}, {'_id':1}) is not None

def dashboard_for_authenticated(cid):
    analysis = dashboard_for(cid) if is_synthetic_customer(cid) else dashboard_for_private(cid)
    analysis['segmentation'] = segment_customer(analysis, segmentation_training_data())
    return analysis

def recommendations_for_authenticated(cid):
    analysis = dashboard_for_authenticated(cid)
    products = product_catalog()
    result = recommend(analysis['metrics'], analysis['financial_state'], products,
                       analysis['financial_stress'], analysis['segmentation'])
    need = analysis['customer'].get('primary_banking_need')
    preferred_categories = {
        'Save': {'Savings'}, 'Borrow': {'Loan', 'Credit'}, 'Invest': {'Investment'},
        'Manage expenses': {'Financial Education'}, 'Protect finances': {'Insurance'},
    }.get(need, set())
    if preferred_categories:
        result['recommendations'].sort(key=lambda item: item['category'] not in preferred_categories)
    result['customer_preferences'] = {
        'primary_banking_need': need,
        'financial_goals': analysis['customer'].get('financial_goals', []),
        'applied_to_ordering': bool(preferred_categories),
    }
    return dict(customer=analysis['customer'], metrics=analysis['metrics'], period=analysis['period'],
                source=analysis['source'], synthetic=analysis['synthetic'], **result)

def transactions_for_authenticated(cid, page=1, limit=20):
    return transactions_for(cid, page, limit) if is_synthetic_customer(cid) else private_transactions_for(cid, page, limit)

def ledger_for_authenticated(cid):
    return load_ledger(cid) if is_synthetic_customer(cid) else load_private_ledger(cid)

def load_private_ledger(cid):
    user = get_collection('users').find_one({'customer_id':cid, 'synthetic': {'$ne': True}}, dict(USER_FIELDS))
    if user is None:
        raise NotFound('Customer not found.')
    profile = get_collection('customer_profiles').find_one({'customer_id':cid}, {'_id':0})
    if profile is None:
        raise Conflict('Customer onboarding is incomplete.')
    rows = list(get_collection('transactions').find({'customer_id':cid, 'synthetic': {'$ne': True}}, dict(TX_FIELDS)).sort([('date',1),('transaction_id',1)]))
    return user, rows, profile

def dashboard_for_private(cid):
    analysis = analyse(*load_private_ledger(cid))
    analysis.update(source='onboarding', synthetic=False)
    return analysis

def recommendations_for_private(cid):
    analysis = dashboard_for_private(cid)
    analysis['segmentation'] = segment_customer(analysis, segmentation_training_data())
    result = recommend(analysis['metrics'], analysis['financial_state'], product_catalog(),
                       analysis['financial_stress'], analysis['segmentation'])
    return dict(customer=analysis['customer'], metrics=analysis['metrics'], period=analysis['period'], source='onboarding', synthetic=False, **result)

def private_transactions_for(cid, page=1, limit=20):
    load_private_ledger(cid)
    query = {'customer_id':cid, 'synthetic': {'$ne': True}}
    collection = get_collection('transactions'); total = collection.count_documents(query)
    rows = list(collection.find(query, dict(TX_FIELDS)).sort([('date',-1),('transaction_id',-1)]).skip((page-1)*limit).limit(limit))
    return dict(customer_id=cid, transactions=rows, page=page, limit=limit, total=total, pages=(total+limit-1)//limit,
                source='onboarding', synthetic=False)

def load_ledger(cid):
    user = load_customer(cid)
    profile = get_collection('financial_profiles').find_one({'customer_id':cid,'synthetic':True},{'_id':0,'dataset':0})
    if profile is None:
        raise Conflict('Customer history is incomplete. Run the Phase 2 seed command.')
    rows = list(get_collection('transactions').find({'customer_id':cid,'synthetic':True},dict(TX_FIELDS)).sort([('date',1),('transaction_id',1)]))
    if not rows:
        raise Conflict('No transaction history is available for this customer.')
    return user,rows,profile

def dashboard_for(cid):
    return analyse(*load_ledger(cid))

def recommendations_for(cid):
    analysis = dashboard_for(cid)
    analysis['segmentation'] = segment_customer(analysis, segmentation_training_data())
    result = recommend(analysis['metrics'], analysis['financial_state'], product_catalog(),
                       analysis['financial_stress'], analysis['segmentation'])
    return dict(customer=analysis['customer'], metrics=analysis['metrics'], period=analysis['period'],
                source='mongodb', synthetic=True, **result)

def product_catalog():
    return list(get_collection('products').find(
        {'synthetic':True}, {'_id':0, 'dataset':0, 'synthetic':0}
    ).sort('product_id', 1))

def segmentation_training_data():
    analyses = []
    ids = get_collection('users').find({'synthetic':True}, {'_id':0, 'customer_id':1}).sort('customer_id', 1)
    for row in ids:
        try:
            analyses.append(analyse(*load_ledger(row['customer_id'])))
        except Conflict:
            continue
    return analyses

def transactions_for(cid,page=1,limit=20):
    load_customer(cid)
    collection = get_collection('transactions')
    query = {'customer_id':cid,'synthetic':True}
    total = collection.count_documents(query)
    rows = list(collection.find(query,dict(TX_FIELDS)).sort([('date',-1),('transaction_id',-1)]).skip((page-1)*limit).limit(limit))
    return dict(customer_id=cid,transactions=rows,page=page,limit=limit,total=total,pages=(total+limit-1)//limit,source='mongodb',synthetic=True)
