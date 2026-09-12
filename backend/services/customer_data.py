from werkzeug.exceptions import NotFound, Conflict
from db import get_collection
from utils.validation import customer_id
from services.financial_health import analyse
from services.recommendations import recommend

USER_FIELDS = {'_id':0,'dataset':0}
TX_FIELDS = {'_id':0,'dataset':0,'synthetic':0}

def list_customers():
    return list(get_collection('users').find({'synthetic':True},{'_id':0,'customer_id':1,'name':1,'city':1,'language':1}).sort('customer_id',1))

def load_customer(cid):
    customer_id(cid)
    user = get_collection('users').find_one({'customer_id':cid,'synthetic':True},USER_FIELDS)
    if user is None:
        raise NotFound('Synthetic customer not found.')
    return user

def load_ledger(cid):
    user = load_customer(cid)
    profile = get_collection('financial_profiles').find_one({'customer_id':cid,'synthetic':True},{'_id':0,'dataset':0})
    if profile is None:
        raise Conflict('Customer history is incomplete. Run the Phase 2 seed command.')
    rows = list(get_collection('transactions').find({'customer_id':cid,'synthetic':True},TX_FIELDS).sort([('date',1),('transaction_id',1)]))
    if not rows:
        raise Conflict('No transaction history is available for this customer.')
    return user,rows,profile

def dashboard_for(cid):
    return analyse(*load_ledger(cid))

def recommendations_for(cid):
    analysis = dashboard_for(cid)
    products = list(get_collection('products').find(
        {'synthetic':True}, {'_id':0, 'dataset':0, 'synthetic':0}
    ).sort('product_id', 1))
    result = recommend(analysis['metrics'], analysis['financial_state'], products)
    return dict(customer=analysis['customer'], metrics=analysis['metrics'], period=analysis['period'],
                source='mongodb', synthetic=True, **result)

def transactions_for(cid,page=1,limit=20):
    load_customer(cid)
    collection = get_collection('transactions')
    query = {'customer_id':cid,'synthetic':True}
    total = collection.count_documents(query)
    rows = list(collection.find(query,TX_FIELDS).sort([('date',-1),('transaction_id',-1)]).skip((page-1)*limit).limit(limit))
    return dict(customer_id=cid,transactions=rows,page=page,limit=limit,total=total,pages=(total+limit-1)//limit,source='mongodb',synthetic=True)
