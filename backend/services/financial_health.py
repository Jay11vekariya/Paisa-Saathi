"""Cash-flow wellness analytics from validated ledger rows; amounts in INR."""
import calendar
import math
import statistics
from collections import defaultdict

from services.financial_state import determine_state, insight_for
from utils.validation import validate_transaction

def clamp(value):
    return max(0,min(100,value))

def stability(values):
    mean = statistics.mean(values) if values else 0
    return clamp(100 * (1 - statistics.pstdev(values)/mean)) if mean > 0 else 0

def change(current, previous):
    # A percentage against zero or negative savings is misleading; expose INR change separately.
    return round((current-previous)/previous*100,1) if previous > 0 else None

def months_between(start,end):
    sy,sm = map(int,start.split('-')); ey,em = map(int,end.split('-'))
    return [f'{n//12:04d}-{n%12+1:02d}' for n in range(sy*12+sm-1,ey*12+em)]

def analyse(customer, transactions, profile):
    months = months_between(profile['period_start'],profile['period_end'])
    buckets = {month:{'month':month,'income':0.0,'expenses':0.0,'emi_paid':0.0} for month in months}
    categories, daily = defaultdict(float), defaultdict(float)
    ledger = []
    for t in transactions:
        validate_transaction(t)
        if t['customer_id'] != customer['customer_id']:
            raise ValueError('Ledger customer mismatch.')
        month = t['date'][:7]
        if month not in buckets:
            continue
        ledger.append(t)
        b = buckets[month]
        b['income' if t['type']=='credit' else 'expenses'] += t['amount']
        if t['type']=='debit':
            if t['category']=='EMI':
                b['emi_paid'] += t['amount']
            if month == months[-1]:
                categories[t['category']] += t['amount']
                daily[t['date']] += t['amount']
    baseline = profile.get('baseline')
    balance = profile['opening_balance']
    history = []
    for month in months:
        b = buckets[month]
        b['savings'] = b['income'] - b['expenses']
        balance += b['savings']
        b['balance'] = balance
        history.append({k:round(v,2) if isinstance(v,float) else v for k,v in b.items()})
    if baseline and not transactions:
        # A new user has stated a monthly baseline, not fabricated ledger activity.
        cur = history[-1]
        cur.update(income=float(baseline['monthly_income']), expenses=float(baseline['monthly_expenses']),
                   emi_paid=0.0, savings=float(baseline['monthly_income'])-float(baseline['monthly_expenses']),
                   balance=float(baseline['account_balance']))
        history[-1] = cur
        balance = cur['balance']
    cur = history[-1]
    prev = history[-2] if len(history)>1 else {'income':0,'expenses':0,'savings':0,'emi_paid':0,'balance':profile['opening_balance']}
    average = statistics.mean(h['expenses'] for h in history)
    previous_income = statistics.mean(h['income'] for h in history[:-1]) if len(history)>1 else cur['income']
    income_stability = stability([h['income'] for h in history])
    expense_stability = stability([h['expenses'] for h in history])
    savings_rate = cur['savings']/cur['income']*100 if cur['income'] else (-100 if cur['expenses'] else 0)
    emi_burden = customer['monthly_emi']/cur['income']*100 if cur['income'] else (100 if customer['monthly_emi'] else 0)
    buffer = max(0,balance)/average if average else 0
    metrics = dict(monthly_income=cur['income'],monthly_expenses=cur['expenses'],monthly_savings=cur['savings'],
        savings_rate=round(savings_rate,1),average_monthly_expenses=round(average,2),
        monthly_emi=customer['monthly_emi'],emi_paid=cur['emi_paid'],emi_burden=round(emi_burden,1),
        income_stability=round(income_stability,1),expense_stability=round(expense_stability,1),
        account_balance=round(balance,2),balance_change=round(cur['balance']-prev['balance'],2),
        emergency_buffer_months=round(buffer,2),income_change_pct=change(cur['income'],prev['income']),
        expense_change_pct=change(cur['expenses'],prev['expenses']),savings_change_pct=change(cur['savings'],prev['savings']),
        savings_change_amount=round(cur['savings']-prev['savings'],2),emi_change_pct=change(cur['emi_paid'],prev['emi_paid']),
        income_disruption=cur['income'] < .65*previous_income if previous_income else cur['income']==0,
        emi_payment_gap=customer['monthly_emi']>0 and cur['emi_paid'] < .9*customer['monthly_emi'])
    parts = [
      ('income','Income Stability',25,income_stability if cur['income']>0 else 0,
       f'Income variability across {len(months)} completed months; months without income count as zero.'),
      ('savings','Savings Behaviour',25,clamp(savings_rate/30*100),'A 30% retained-income rate receives full points; negative savings receive zero.'),
      ('debt','Debt Burden',20,clamp(100-emi_burden/60*100),'Full points at zero EMI burden, falling linearly to zero at 60% of income.'),
      ('expenses','Expense Stability',15,expense_stability,'One minus the coefficient of variation of monthly outgoings.'),
      ('buffer','Emergency Buffer',15,clamp(buffer/6*100),'Six months of average outgoings in the closing balance receives full points.')]
    factors = [dict(key=k,label=label,weight=weight,score=round(score,1),contribution=round(score*weight/100,2),explanation=explanation)
               for k,label,weight,score,explanation in parts]
    score = math.floor(sum(f['contribution'] for f in factors)+.5)
    health = dict(score=score,status='Strong' if score>=80 else 'Healthy' if score>=60 else 'Caution' if score>=40 else 'Needs Support',
                  factors=factors,methodology='Prototype financial wellness score, not a credit score or loan eligibility assessment.',
                  positive_factors=[f['label'] for f in factors if f['score']>=75],
                  areas_to_review=[f['label'] for f in factors if f['score']<60])
    state = determine_state(metrics)
    year, month = map(int,months[-1].split('-'))
    daily_series = [dict(date=f'{months[-1]}-{day:02d}',amount=round(daily[f'{months[-1]}-{day:02d}'],2))
                    for day in range(1,calendar.monthrange(year,month)[1]+1)]
    category_rows = [dict(name=k,amount=round(v,2),percentage=round(v/cur['expenses']*100,1) if cur['expenses'] else 0)
                     for k,v in sorted(categories.items(),key=lambda pair:pair[1],reverse=True)]
    return dict(customer=customer,financial_health=health,financial_state=state,metrics=metrics,
                spending=dict(categories=category_rows,daily=daily_series,monthly=history),
                recent_transactions=sorted(ledger,key=lambda t:(t['date'],t['transaction_id']),reverse=True)[:5],
                insight=insight_for(state,metrics),period=dict(start=months[0],month=months[-1],complete=True),
                source='mongodb',synthetic=True)

