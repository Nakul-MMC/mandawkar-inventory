from models import db, Payment, Invoice, Purchase, Customer, Dealer
from datetime import datetime

def record_customer_payment(customer_id, amount, method, notes, date=None):
    """
    Records a payment from a customer.
    Logic:
    1. Create Payment record.
    2. Auto-allocate amount to oldest 'Pending' invoices (FIFO).
    3. Update Invoice statuses.
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # 1. Create Logic Log
    pay = Payment(
        type='Receivable',
        party_type='Customer',
        party_id=customer_id,
        amount=amount,
        date=date,
        method=method,
        notes=notes
    )
    db.session.add(pay)
    
    # 2. Allocate to Invoices
    # Get unpaid invoices, ordered by date (Oldest first)
    invoices = Invoice.query.filter(
        Invoice.customer_id == customer_id,
        Invoice.status != 'Paid',
        Invoice.is_active == True
    ).order_by(Invoice.created_at).all()
    
    remaining = amount
    
    for inv in invoices:
        if remaining <= 0:
            break
            
        due = inv.total - inv.paid_amount
        to_pay = min(remaining, due)
        
        inv.paid_amount += to_pay
        remaining -= to_pay
        
        if inv.paid_amount >= inv.total:
            inv.status = 'Paid'
        else:
            inv.status = 'Partial'
            
    db.session.commit()
    return True

def record_dealer_payment(dealer_id, amount, method, notes, date=None):
    """
    Records a payment TO a dealer.
    Same FIFO logic as customer.
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    # 1. Create Logic Log
    pay = Payment(
        type='Payable',
        party_type='Dealer',
        party_id=dealer_id,
        amount=amount,
        date=date,
        method=method,
        notes=notes
    )
    db.session.add(pay)
    
    # 2. Allocate to Purchases
    purchases = Purchase.query.filter(
        Purchase.dealer_id == dealer_id,
        Purchase.status != 'Paid'
    ).order_by(Purchase.date).all()
    
    remaining = amount
    
    for pur in purchases:
        if remaining <= 0:
            break
            
        due = pur.total_amount - pur.paid_amount
        to_pay = min(remaining, due)
        
        pur.paid_amount += to_pay
        remaining -= to_pay
        
        if pur.paid_amount >= pur.total_amount:
            pur.status = 'Paid'
        else:
            pur.status = 'Partial'
            
    db.session.commit()
    return True
