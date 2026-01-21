from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, get_flashed_messages, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
from werkzeug.security import check_password_hash
from utils.export_excel import export_inventory_to_excel
import uuid
import os

app = Flask(__name__)
app.secret_key = "mandawkar-secret-key"  # required for sessions

from models import db, User, Product, Category, Invoice, InvoiceItem, AuditLog
import os

app = Flask(__name__)
app.secret_key = "mandawkar-secret-key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Ensure DB tables exist
with app.app_context():
    db.create_all()
    
    # Create Default Admin if no users exist
    if not User.query.first():
        from werkzeug.security import generate_password_hash
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Default 'admin' user created.")

from models import Customer, Dealer, Purchase, PurchaseItem, Payment
from utils.finance import record_customer_payment, record_dealer_payment


# =========================
# AUTH DECORATOR
# =========================
def login_required(role=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                return "Access Denied", 403
            return func(*args, **kwargs)
        return wrapper
    return decorator


# =========================
# LOGIN / LOGOUT
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user"] = user.username
            session["role"] = user.role
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =========================
# DASHBOARD
# =========================
@app.route("/")
@login_required()
def dashboard():
    # Total quantity (Active products only)
    total_quantity = db.session.query(db.func.sum(Product.quantity)).filter(Product.is_active==True).scalar() or 0
    
    # Total value
    total_value = db.session.query(db.func.sum(Product.quantity * Product.price)).filter(Product.is_active==True).scalar() or 0

    # Summary List (Distinct products)
    products = Product.query.filter(Product.is_active==True).order_by(Product.category, Product.size).all()
    
    # Map ORM objects to list format expected by template [cat, size, type, variant, qty, value, threshold]
    summary = []
    for p in products:
        variant_display = p.pattern if (p.pattern and p.pattern.strip()) else p.variant
        summary.append([
            p.category, 
            p.size, 
            p.type, 
            variant_display, 
            p.quantity, 
            p.quantity * p.price,
            p.threshold
        ])

    # Low Stock Count
    low_stock_count = Product.query.filter(Product.is_active==True, Product.quantity <= Product.threshold).count()

    return render_template(
        "dashboard.html",
        total_quantity=total_quantity,
        total_value=round(total_value, 2),
        summary=summary,
        low_stock_count=low_stock_count
    )


# =========================
# CATEGORIES (ADMIN ONLY)
# =========================
@app.route("/categories", methods=["GET", "POST"])
@login_required("admin")
def categories():
    error = None

    if request.method == "POST" and "add" in request.form:
        name = request.form["name"].strip()
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
            db.session.commit()

    if request.method == "POST" and "delete" in request.form:
        category_id = request.form["category_id"]
        category = Category.query.get(category_id)
        
        # Check if products exist
        count = Product.query.filter_by(category=category.name, is_active=True).count()

        if count > 0:
            error = "Cannot delete category. Products exist under this category."
        else:
            if category:
                db.session.delete(category)
                db.session.commit()

    categories = Category.query.order_by(Category.name).all()
    # Template expects tuples or objects. SQLAlchemy returns objects.
    # To minimize template changes, I'll pass objects. Template uses c[1]? No, template usually uses c.name or c[1].
    # Let's check format. Original was `select *`, so (id, name).
    # If template uses c[1], we need to adapt or fixing template.
    # Let's assume user wants me to fix code. I will fix template too if needed. 
    # Actually, let's keep it safe:
    categories_list = [(c.id, c.name) for c in categories]

    return render_template("categories.html", categories=categories_list, error=error)


# =========================
# ADD PRODUCT
# =========================
@app.route("/add-product", methods=["GET", "POST"])
@login_required()
def add_product():
    if request.method == "POST":
        new_product = Product(
            category=request.form["category"],
            size=request.form.get("size"),
            type=request.form.get("type"),
            variant=request.form.get("variant"),
            pattern=request.form.get("pattern"),
            quantity=int(request.form["quantity"]),
            threshold=int(request.form["threshold"]),
            price=float(request.form["price"]),
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_active=True
        )
        db.session.add(new_product)
        db.session.commit()
        
        # Log Action
        log = AuditLog(user=session.get('user'), action='CREATE', target=f'Product', details=f'Added {new_product.category} {new_product.size}')
        db.session.add(log)
        db.session.commit()

        return redirect(url_for("inventory"))

    categories = Category.query.order_by(Category.name).all()
    categories_list = [(c.id, c.name) for c in categories] # Maintain tuple format for template

    return render_template("add_product.html", categories=categories_list)


# =========================
# INVENTORY
# =========================
@app.route("/inventory")
@login_required()
def inventory():
    category = request.args.get("category")

    query = Product.query.filter(Product.is_active==True)
    if category:
        query = query.filter(Product.category == category)
    
    products_obj = query.all()
    
    # Map to tuple/list for template compatibility
    # [id, category, size, type, variant, pattern, quantity, threshold, price, last_updated]
    products = []
    for p in products_obj:
        products.append((
            p.id, p.category, p.size, p.type, p.variant, p.pattern, 
            p.quantity, p.threshold, p.price, p.last_updated
        ))

    return render_template(
        "inventory.html",
        products=products,
        selected_category=category
    )


# =========================
# EDIT PRODUCT
# =========================
@app.route("/edit/<int:product_id>", methods=["GET", "POST"])
@login_required()
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        product.quantity = int(request.form["quantity"])
        product.threshold = int(request.form["threshold"])
        product.price = float(request.form["price"])
        product.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        db.session.commit()
        
        # Log
        db.session.add(AuditLog(user=session.get('user'), action='UPDATE', target=f'Product {product.id}', details=f'Updated Qty: {product.quantity}'))
        db.session.commit()

        return redirect(url_for("inventory"))

    # Map to tuple for template
    product_tuple = (
        product.id, product.category, product.size, product.type, product.variant, 
        product.pattern, product.quantity, product.threshold, product.price, product.last_updated
    )

    return render_template("edit_product.html", product=product_tuple)


# =========================
# DELETE PRODUCT
# =========================
@app.route("/delete-product/<int:product_id>", methods=["POST"])
@login_required("admin")
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Soft Delete
    product.is_active = False
    db.session.commit()
    
    # Log
    db.session.add(AuditLog(user=session.get('user'), action='DELETE', target=f'Product {product.id}', details='Soft Deleted'))
    db.session.commit()

    return redirect(url_for("inventory"))


# =========================
# EXPORT TO EXCEL
# =========================
@app.route("/export")
@login_required()
def export():
    filename = export_inventory_to_excel()
    return f"""
        <h3>Export Successful</h3>
        <p>File saved at:</p>
        <b>{filename}</b><br><br>
        <a href="/inventory">Back to Inventory</a>
    """
# =========================
# Invoice
# =========================
@app.route("/invoice", methods=["GET", "POST"])
@login_required("admin")
def create_invoice():
    if request.method == "POST":
        try:
            subtotal = 0
            items = []
            
            # Fetch all active products
            all_products = Product.query.filter_by(is_active=True).all()
            
            # 1. Validation & Calculation Phase
            for p in all_products:
                qty_str = request.form.get(f"qty_{p.id}")
                if qty_str and int(qty_str) > 0:
                    qty = int(qty_str)
                    
                    # Stock Check
                    if qty > p.quantity:
                        return f"Not enough stock for {p.category} {p.size}", 400

                    # Description
                    description_parts = [p.category, p.type, p.size, p.pattern or p.variant]
                    description = " - ".join([str(x) for x in description_parts if x])

                    # Custom Price Logic
                    custom_price = float(request.form.get(f"price_{p.id}", p.price))
                    
                    line_total = qty * custom_price
                    subtotal += line_total

                    items.append({
                        "product": p,
                        "description": description,
                        "quantity": qty,
                        "price": custom_price,
                        "total": line_total
                    })

            if not items:
                return "No items selected", 400

            # 2. Totals Calculation
            discount_input = float(request.form["discount"])
            discount = subtotal * discount_input / 100 if discount_input <= 100 else discount_input
            taxable_value = subtotal - discount

            enable_cgst = "enable_cgst" in request.form
            enable_sgst = "enable_sgst" in request.form
            cgst_percent = float(request.form["cgst_percent"]) if enable_cgst else 0
            sgst_percent = float(request.form["sgst_percent"]) if enable_sgst else 0

            cgst_amount = taxable_value * cgst_percent / 100
            sgst_amount = taxable_value * sgst_percent / 100
            total = taxable_value + cgst_amount + sgst_amount

            # 3. Execution Phase (Atomic Transaction)
            invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
            
            # Find or Create Customer
            customer_name_input = request.form["customer_name"].strip()
            customer_obj = Customer.query.filter_by(name=customer_name_input).first()
            if not customer_obj:
                customer_obj = Customer(
                    name=customer_name_input, 
                    gstin=request.form["customer_gstin"],
                    phone="N/A", # Optional, can improve frontend to capture this
                    address="Created via Invoice"
                )
                db.session.add(customer_obj)
                db.session.flush() # Get ID
            
            new_invoice = Invoice(
                invoice_number=invoice_number,
                customer_name=customer_name_input,
                customer_gstin=request.form["customer_gstin"],
                subtotal=subtotal,
                discount=discount,
                cgst_percent=cgst_percent,
                cgst_amount=cgst_amount,
                sgst_percent=sgst_percent,
                sgst_amount=sgst_amount,
                taxable_value=taxable_value,
                total=total,
                created_at=request.form["invoice_date"] + " " + datetime.now().strftime("%H:%M:%S"),
                is_active=True,
                customer_id=customer_obj.id, # Link to Finance Module
                paid_amount=0.0, # Default to Unpaid
                status='Pending'
            )
            db.session.add(new_invoice)
            db.session.flush() # Get ID

            for item in items:
                # Add Line Item
                inv_item = InvoiceItem(
                    invoice_id=new_invoice.id,
                    product_id=item["product"].id,
                    product_name=item["description"],
                    quantity=item["quantity"],
                    price=item["price"],
                    total=item["total"]
                )
                db.session.add(inv_item)

                # Deduct Stock
                p = item["product"]
                p.quantity -= item["quantity"] # SQLAlchemy tracks this change
            
            db.session.commit() # Commit everything together
            
            # Log
            db.session.add(AuditLog(user=session.get('user'), action='CREATE', target=f'Invoice {invoice_number}', details=f'Total: {total}'))
            db.session.commit()

            return render_template("invoice_success.html", invoice_id=new_invoice.id, invoice_number=invoice_number)

        except Exception as e:
            db.session.rollback() # Rollback EVERYTHING on error
            return f"Error creating invoice: {str(e)}", 500

    # GET request
    products_obj = Product.query.filter_by(is_active=True).all()
    # Map to tuple for template
    products = []
    for p in products_obj:
        products.append((
            p.id, p.category, p.size, p.type, p.variant, p.pattern, 
            p.quantity, p.threshold, p.price, p.last_updated
        ))

    return render_template(
        "create_invoice.html",
        products=products,
        customers=Customer.query.filter_by(is_active=True).all(),
        today=datetime.now().strftime("%Y-%m-%d")
    )



@app.route("/invoices")
@login_required("admin")
def invoice_history():
    invoices_obj = Invoice.query.filter_by(is_active=True).order_by(Invoice.created_at.desc()).all()
    
    # Map to tuples for template (match expected list format)
    # [id, invoice_number, customer_name, customer_gstin, total, created_at]
    invoices = []
    for i in invoices_obj:
        invoices.append((
            i.id,
            i.invoice_number,
            i.customer_name,
            i.customer_gstin,
            i.total,
            i.created_at
        ))

    return render_template("invoice_history.html", invoices=invoices)


@app.route("/api/invoice/<int:invoice_id>")
@login_required("admin")
def get_invoice_details(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    items = InvoiceItem.query.filter_by(invoice_id=invoice.id).all()
    
    items_data = []
    for item in items:
        items_data.append({
            "description": item.product_name,
            "quantity": item.quantity,
            "price": item.price,
            "total": item.total
        })
        
    return jsonify({
        "invoice_number": invoice.invoice_number,
        "date": invoice.created_at,
        "customer_name": invoice.customer_name,
        "customer_gstin": invoice.customer_gstin,
        "items": items_data,
        "subtotal": invoice.subtotal,
        "discount": invoice.discount,
        "tax_amount": invoice.cgst_amount + invoice.sgst_amount,
        "total": invoice.total,
        "id": invoice.id
    })



@app.route("/download-invoice/<int:invoice_id>")
@login_required("admin")
def download_invoice(invoice_id):
    from utils.new_invoice_pdf import generate_invoice_pdf
    file_path = generate_invoice_pdf(invoice_id)
    return send_file(file_path, as_attachment=True)



@app.route("/sales-report")
@login_required("admin")
def sales_report():
    # Queries using SQLAlchemy core for aggregations
    
    # Daily
    # SQLite DATE() works in raw SQL. In ORM, func.date
    daily = db.session.query(
        db.func.date(Invoice.created_at), db.func.sum(Invoice.total)
    ).filter(Invoice.is_active==True).group_by(db.func.date(Invoice.created_at)).all()

    # Monthly
    monthly = db.session.query(
        db.func.strftime('%Y-%m', Invoice.created_at), db.func.sum(Invoice.total)
    ).filter(Invoice.is_active==True).group_by(db.func.strftime('%Y-%m', Invoice.created_at)).all()

    # GST
    gst = db.session.query(
        db.func.sum(Invoice.cgst_amount), db.func.sum(Invoice.sgst_amount)
    ).filter(Invoice.is_active==True).first()

    return render_template(
        "sales_report.html",
        daily=daily,
        monthly=monthly,
        gst=gst
    )




# =========================
# FINANCE ROUTES
# =========================
@app.route("/finance")
@login_required()
def finance():
    # 1. Customer Receivables Summary
    customers = Customer.query.filter_by(is_active=True).all()
    receivables = []
    total_receivable = 0
    total_received = 0
    
    for c in customers:
        # Aggregate Invoices
        invoices = Invoice.query.filter_by(customer_id=c.id, is_active=True).all()
        bill_sum = sum(i.total for i in invoices)
        paid_sum = sum(i.paid_amount for i in invoices)
        due = bill_sum - paid_sum
        
        if bill_sum > 0: # Only show active customers
            receivables.append({
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "total_bill": bill_sum,
                "paid": paid_sum,
                "due": due,
                "status": "Paid" if due <= 1 else ("Partial" if paid_sum > 0 else "Pending")
            })
            total_receivable += due
            total_received += paid_sum

    # 2. Dealer Payables Summary
    dealers = Dealer.query.filter_by(is_active=True).all()
    payables = []
    total_payable = 0
    total_paid = 0
    
    for d in dealers:
        purchases = Purchase.query.filter_by(dealer_id=d.id).all()
        buy_sum = sum(p.total_amount for p in purchases)
        paid_sum = sum(p.paid_amount for p in purchases)
        due = buy_sum - paid_sum
        
        if buy_sum > 0:
            payables.append({
                "id": d.id,
                "name": d.name,
                "phone": d.phone,
                "total_buy": buy_sum,
                "paid": paid_sum,
                "due": due,
                "status": "Paid" if due <= 1 else ("Partial" if paid_sum > 0 else "Pending")
            })
            total_payable += due
            total_paid += paid_sum

    # Sort: Pending(0) > Partial(1) > Paid(2)
    def get_priority(item):
        s = item['status']
        if s == 'Pending': return 0
        if s == 'Partial': return 1
        return 2

    receivables.sort(key=get_priority)
    payables.sort(key=get_priority)

    return render_template(
        "finance.html",
        receivables=receivables,
        payables=payables,
        total_receivable=total_receivable,
        total_payable=total_payable,
        today=datetime.now().strftime("%Y-%m-%d")
    )

@app.route("/api/add-customer", methods=["POST"])
@login_required("admin")
def add_customer():
    try:
        name = request.form["name"]
        phone = request.form.get("phone", "")
        gstin = request.form.get("gstin", "")
        address = request.form.get("address", "")
        
        if Customer.query.filter_by(name=name).first():
            return "Customer already exists", 400
            
        new_c = Customer(name=name, phone=phone, gstin=gstin, address=address)
        db.session.add(new_c)
        db.session.commit()
        return redirect(url_for("finance"))
    except Exception as e:
        return f"Error: {e}", 500

@app.route("/api/add-dealer", methods=["POST"])
@login_required("admin")
def add_dealer():
    try:
        name = request.form["name"]
        phone = request.form.get("phone", "")
        gstin = request.form.get("gstin", "")
        
        if Dealer.query.filter_by(name=name).first():
            return "Dealer already exists", 400
            
        new_d = Dealer(name=name, phone=phone, gstin=gstin)
        db.session.add(new_d)
        db.session.commit()
        return redirect(url_for("finance"))
    except Exception as e:
        return f"Error: {e}", 500

@app.route("/api/record-payment", methods=["POST"])
@login_required("admin")
def record_payment():
    try:
        type_ = request.form["type"] # 'Customer' or 'Dealer'
        id_ = int(request.form["id"])
        amount = float(request.form["amount"])
        method = request.form["method"]
        notes = request.form.get("notes", "")
        date = request.form["date"]
        
        if type_ == "Customer":
            record_customer_payment(id_, amount, method, notes, date)
        elif type_ == "Dealer":
            record_dealer_payment(id_, amount, method, notes, date)
            
        return redirect(url_for("finance"))
    except Exception as e:
        return f"Error recording payment: {e}", 500

@app.route("/record-purchase", methods=["GET", "POST"])
@login_required("admin")
def record_purchase():
    if request.method == "POST":
        try:
            # 1. Find or Create Dealer
            dealer_name = request.form["dealer_name"].strip()
            dealer_obj = Dealer.query.filter_by(name=dealer_name).first()
            if not dealer_obj:
                dealer_obj = Dealer(name=dealer_name, address="Created via Purchase")
                db.session.add(dealer_obj)
                db.session.flush()

            # 2. Process Items (Original Logic)
            items = []
            total_amount = 0
            
            for key, value in request.form.items():
                if key.startswith("qty_") and value:
                    try:
                        qty = int(value)
                    except ValueError:
                        continue # Skip if not a valid number
                    
                    if qty > 0:
                        product_id = int(key.split("_")[1])
                        # Get Cost (if provided, otherwise 0)
                        cost_val = request.form.get(f"cost_{product_id}")
                        cost = float(cost_val) if cost_val else 0.0
                        
                        line_total = qty * cost
                        total_amount += line_total
                        
                        items.append({
                            "product_id": product_id,
                            "qty": qty,
                            "cost": cost,
                            "total": line_total
                        })

            if not items:
                # Fallback / Error if no items found
                # Or maybe user just wanted to record a bill without items? (Unlikely)
                pass

            # 3. Create Purchase Record
            paid_amount = float(request.form.get("paid_amount", 0))
            status = 'Paid' if paid_amount >= total_amount else ('Partial' if paid_amount > 0 else 'Pending')
            
            new_purchase = Purchase(
                dealer_id=dealer_obj.id,
                invoice_number=request.form["invoice_number"],
                date=request.form["date"],
                total_amount=total_amount,
                paid_amount=paid_amount,
                status=status
            )
            db.session.add(new_purchase)
            db.session.flush()

            # 4. Save Items and Update Stock
            for item in items:
                # Add Purchase Item
                pi = PurchaseItem(
                    purchase_id=new_purchase.id,
                    product_id=item["product_id"],
                    product_name="(Ref ID " + str(item["product_id"]) + ")",
                    quantity=item["qty"],
                    cost_price=item["cost"],
                    total_amount=item["total"]
                )
                db.session.add(pi)
                
                # UPDATE STOCK
                p = Product.query.get(item["product_id"])
                if p:
                    p.quantity += item["qty"]
                    # Optionally update cost price behavior if needed
            
            # 5. Record Payment
            if paid_amount > 0:
                payment = Payment(
                    type='Payable', party_type='Dealer', party_id=dealer_obj.id,
                    reference_id=new_purchase.id, amount=paid_amount,
                    date=request.form["date"], method="Initial", notes="Paid during purchase"
                )
                db.session.add(payment)

            db.session.commit()
            return redirect(url_for("finance"))

        except Exception as e:
            db.session.rollback()
            return f"Error recording purchase: {e}", 500

    # Fetch products for Datalist
    products_obj = Product.query.filter_by(is_active=True).all()
    
    # Fetch Categories for New Product Modal
    categories_obj = Category.query.order_by(Category.name).all()
    category_names = [c.name for c in categories_obj]

    return render_template(
        "record_purchase.html",
        products=products_obj,
        dealers=Dealer.query.filter_by(is_active=True).all(),
        categories=category_names,
        today=datetime.now().strftime("%Y-%m-%d")
    )

@app.route("/api/quick-add-product", methods=["POST"])
@login_required("admin")
def quick_add_product():
    data = request.json
    try:
        new_prod = Product(
            category=data.get('category'),
            size=data.get('size'),
            type=data.get('type'),
            variant=data.get('variant'),
            pattern=data.get('pattern'),
            price=float(data.get('price', 0)),
            threshold=int(data.get('threshold', 5)),
            quantity=0 # Start with 0, purchase will add
        )
        db.session.add(new_prod)
        db.session.commit()
        return jsonify({"success": True, "id": new_prod.id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# =========================
# OLD EXPORT ROUTE ...
# =========================
@app.route("/export-inventory")
@login_required("admin")
def export_inventory():
    from utils.export_excel import export_inventory_to_excel
    try:
        file_path = export_inventory_to_excel()
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"Error creating export: {str(e)}", 500


# =========================
# START APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
