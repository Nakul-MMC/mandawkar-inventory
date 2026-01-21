from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    size = db.Column(db.String(50))
    type = db.Column(db.String(50))
    variant = db.Column(db.String(100))
    pattern = db.Column(db.String(100))
    quantity = db.Column(db.Integer, nullable=False, default=0)
    threshold = db.Column(db.Integer, nullable=False, default=10)
    price = db.Column(db.Float, nullable=False, default=0.0)
    last_updated = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Soft Delete

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True)
    customer_name = db.Column(db.String(100))
    customer_gstin = db.Column(db.String(50))
    subtotal = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    cgst_percent = db.Column(db.Float, default=0.0)
    cgst_amount = db.Column(db.Float, default=0.0)
    sgst_percent = db.Column(db.Float, default=0.0)
    sgst_amount = db.Column(db.Float, default=0.0)
    taxable_value = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True, nullable=False) # Soft Delete
    
    # Financials
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True) # Check logic for migration
    paid_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Pending') # Paid, Partial, Pending
    
    items = db.relationship('InvoiceItem', backref='invoice', lazy=True)
    customer = db.relationship('Customer', backref='invoices')

class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(200))
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)

# =========================
# FINANCE MODULE MODELS
# =========================

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    gstin = db.Column(db.String(20))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

class Dealer(db.Model):
    __tablename__ = 'dealers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    gstin = db.Column(db.String(20))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    dealer_id = db.Column(db.Integer, db.ForeignKey('dealers.id'), nullable=False)
    invoice_number = db.Column(db.String(50)) # Dealer's invoice number
    date = db.Column(db.String(20), nullable=False)
    total_amount = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Pending') # Paid, Partial, Pending
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    dealer = db.relationship('Dealer', backref='purchases')
    items = db.relationship('PurchaseItem', backref='purchase', lazy=True)

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(200))
    quantity = db.Column(db.Integer, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False) # 'Receivable' (In) or 'Payable' (Out)
    party_type = db.Column(db.String(20), nullable=False) # 'Customer' or 'Dealer'
    party_id = db.Column(db.Integer, nullable=False) # ID of Customer or Dealer
    reference_id = db.Column(db.Integer) # ID of Invoice or Purchase (Optional for generic payments?)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    method = db.Column(db.String(50)) # Cash, UPI, Bank
    notes = db.Column(db.Text)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80))
    action = db.Column(db.String(50)) # CREATE, UPDATE, DELETE
    target = db.Column(db.String(100)) # Product ID, Invoice ID
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
