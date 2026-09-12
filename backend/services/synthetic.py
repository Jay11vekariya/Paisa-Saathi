"""Reproducible nine-month fictional banking histories. No real customer data."""
import calendar
import csv
import random
from datetime import date
from pathlib import Path
from utils.validation import validate_transaction

DATASET = 'paisa-phase2-v1'
PEOPLE = [
 ('Rahul Patel',29,'Ahmedabad','Gujarati',75000,12000,'growth'),
 ('Priya Shah',31,'Surat','Hindi',65000,8000,'normal'),
 ('Ramesh Patel',42,'Rajkot','Gujarati',38000,14000,'caution'),
 ('Aman Verma',27,'Mumbai','Hindi',45000,12500,'support'),
 ('Meera Desai',34,'Vadodara','Gujarati',82000,9000,'growth'),
 ('Arjun Rao',30,'Bengaluru','English',110000,18000,'normal'),
 ('Neha Joshi',26,'Pune','Hindi',52000,6000,'growth'),
 ('Kiran Shah',45,'Ahmedabad','Gujarati',62000,21000,'caution'),
 ('Vivek Sharma',38,'Delhi','Hindi',94000,15000,'normal'),
 ('Isha Mehta',28,'Surat','Gujarati',58000,4500,'growth'),
 ('Dev Patel',33,'Rajkot','Gujarati',47000,12000,'normal'),
 ('Sana Khan',29,'Mumbai','Hindi',72000,26000,'caution'),
 ('Rohan Kulkarni',36,'Pune','English',89000,12000,'growth'),
 ('Anjali Nair',41,'Bengaluru','English',105000,22000,'normal'),
 ('Nitin Solanki',39,'Vadodara','Gujarati',41000,11000,'support'),
 ('Kavya Singh',25,'Delhi','Hindi',49000,5500,'growth'),
 ('Yash Trivedi',32,'Ahmedabad','Gujarati',68000,10500,'normal'),
 ('Pooja Soni',37,'Rajkot','Hindi',57000,18500,'caution'),
 ('Aditya Shah',28,'Surat','Gujarati',76000,9500,'growth'),
 ('Ritu Verma',43,'Mumbai','Hindi',63000,18000,'support'),
]
PRODUCTS = [
 ('PR001','Flexible savings account','Savings','Fictional savings product for dataset testing.',0,'Low','NORMAL'),
 ('PR002','Recurring deposit','Savings','Illustrative regular-deposit product.',15000,'Low','GROWTH'),
 ('PR003','Diversified investment learning plan','Investment','Fictional product; returns are not promised.',30000,'Medium','GROWTH'),
 ('PR004','Family health cover','Insurance','Illustrative cover, with no actual policy terms.',20000,'Low','NORMAL'),
 ('PR005','Education loan example','Loan','Dataset example only; no eligibility decision.',25000,'Medium','NORMAL'),
 ('PR006','Responsible credit guide','Credit','Fictional educational credit product.',18000,'Medium','CAUTION'),
 ('PR007','Cash-flow essentials','Financial Education','Educational budgeting resource placeholder.',0,'Low','SUPPORT'),
 ('PR008','Emergency fund planner','Financial Education','Fictional emergency savings learning resource.',0,'Low','CAUTION'),
]

def completed_months(today=None, count=9):
    today = today or date.today()
    end = today.year * 12 + today.month - 2
    return [f'{n // 12:04d}-{n % 12 + 1:02d}' for n in range(end-count+1, end+1)]

def generate(today=None):
    months = completed_months(today)
    users, transactions, profiles = [], [], []
    weights = [('Food',.17,12,'Swiggy / local groceries'),('Shopping',.12,4,'Amazon / local retail'),
               ('Transport',.08,8,'Metro / fuel'),('Bills',.10,3,'Electricity / mobile'),
               ('Rent',.31,1,'Monthly rent'),('Education',.025,1,'Learning centre'),
               ('Healthcare',.025,1,'Pharmacy'),('Entertainment',.045,3,'Cinema / streaming'),
               ('Investment',.06,1,'Recurring investment'),('UPI Transfer',.045,2,'Household transfer'),
               ('Other',.02,2,'Everyday purchase')]
    for number, (name,age,city,language,income,emi,scenario) in enumerate(PEOPLE,1):
        cid = f'PS{number:03d}'
        rng = random.Random(2026 + number)
        opening = income * (3.4 if scenario == 'growth' else 2 if scenario == 'normal' else .65 if scenario == 'caution' else .3)
        customer_rows = []
        for m, month in enumerate(months):
            year, mon = map(int, month.split('-'))
            last = calendar.monthrange(year,mon)[1]
            serial = 0
            def add(day,kind,category,amount,merchant,method='UPI'):
                nonlocal serial
                serial += 1
                row = {'transaction_id':f'{cid}-{month.replace("-","")}-{serial:03d}','customer_id':cid,
                       'date':f'{month}-{day:02d}','type':kind,'category':category,'amount':round(amount,2),
                       'merchant':merchant,'location':city,'payment_method':method,'synthetic':True,'dataset':DATASET}
                validate_transaction(row)
                customer_rows.append(row)
            earned = income
            if scenario == 'support' and m >= 7:
                earned = round(income * (.55 if m == 7 else .28))
            add(1,'credit','Salary',earned,'Monthly salary','NEFT')
            ratio = {'growth':.51 - m*.013,'normal':.56,
                     'caution':.44 + m*.018,'support':.57}[scenario]
            budget = round(income * ratio)
            # A deliberate rising-expense pattern, not random state labels.
            if scenario == 'caution' and m == 8:
                budget = round(budget * 1.14)
            for category,weight,count,merchant in weights:
                category_total = round(budget * weight)
                portions = [rng.uniform(.7,1.3) for _ in range(count)]
                remaining = category_total
                for k, portion in enumerate(portions):
                    amount = remaining if k == count-1 else round(category_total * portion/sum(portions),2)
                    remaining = round(remaining-amount,2)
                    add(min(last, 2 + int(k*(last-3)/max(1,count-1)) + rng.randint(0,1)),
                        'debit',category,amount,merchant,'UPI' if category != 'Rent' else 'NEFT')
            if not (scenario == 'support' and m == 8):
                add(5,'debit','EMI',emi,'Scheduled loan EMI','Auto debit')
        net = sum(t['amount'] * (1 if t['type']=='credit' else -1) for t in customer_rows)
        users.append({'customer_id':cid,'name':name,'age':age,'city':city,'language':language,
                      'monthly_income':income,'employment_type':'Salaried','monthly_emi':emi,
                      'account_balance':round(opening+net,2),'synthetic':True,'dataset':DATASET})
        profiles.append({'customer_id':cid,'opening_balance':opening,'period_start':months[0],
                         'period_end':months[-1],'synthetic':True,'dataset':DATASET})
        transactions.extend(customer_rows)
    products = [dict(zip(('product_id','product_name','category','description','minimum_income','risk_level','ideal_customer_state'),row),
                     synthetic=True,dataset=DATASET) for row in PRODUCTS]
    return {'users':users,'transactions':transactions,'financial_profiles':profiles,'products':products}

def write_csv(data, directory=None):
    directory = directory or Path(__file__).resolve().parents[2] / 'data'
    directory.mkdir(exist_ok=True)
    for collection, filename in [('users','customers'),('transactions','transactions'),('products','products')]:
        rows = data[collection]
        fields = [key for key in rows[0] if key not in ('dataset','synthetic')]
        with (directory / f'{filename}.csv').open('w',newline='',encoding='utf-8') as file:
            writer = csv.DictWriter(file,fieldnames=fields,extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)

