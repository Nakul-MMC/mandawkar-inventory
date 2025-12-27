from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from functools import wraps
from werkzeug.security import check_password_hash
from utils.db import create_tables, get_connection
from utils.export_excel import export_inventory_to_excel
from utils.invoice_pdf import generate_invoice_pdf
from flask import send_file
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mandawkar-secret-key"  # required for sessions

# Initialize DB
create_tables()


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
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (request.form["username"],)
        )
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], request.form["password"]):
            session["user"] = user[1]
            session["role"] = user[3]
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
    conn = get_connection()
    cursor = conn.cursor()

    # Total quantity
    cursor.execute("SELECT SUM(quantity) FROM products")
    total_quantity = cursor.fetchone()[0] or 0

    # Total value
    cursor.execute("SELECT SUM(quantity * price) FROM products")
    total_value = cursor.fetchone()[0] or 0

    # Inventory-level summary
    cursor.execute("""
        SELECT
            category,
            size,
            type,
            COALESCE(pattern, variant),
            SUM(quantity) AS qty,
            SUM(quantity * price) AS value
        FROM products
        GROUP BY category, size, type, COALESCE(pattern, variant)
        ORDER BY category, size
    """)
    summary = cursor.fetchall()

    # 🔴 LOW STOCK COUNT (THIS WAS MISSING)
    cursor.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE quantity <= threshold
    """)
    low_stock_count = cursor.fetchone()[0]

    conn.close()

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
    conn = get_connection()
    cursor = conn.cursor()
    error = None

    if request.method == "POST" and "add" in request.form:
        cursor.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            (request.form["name"].strip(),)
        )
        conn.commit()

    if request.method == "POST" and "delete" in request.form:
        category_id = request.form["category_id"]

        cursor.execute("""
            SELECT COUNT(*) FROM products
            WHERE category = (SELECT name FROM categories WHERE id = ?)
        """, (category_id,))
        count = cursor.fetchone()[0]

        if count > 0:
            error = "Cannot delete category. Products exist under this category."
        else:
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            conn.commit()

    cursor.execute("SELECT * FROM categories ORDER BY name")
    categories = cursor.fetchall()
    conn.close()

    return render_template("categories.html", categories=categories, error=error)


# =========================
# ADD PRODUCT
# =========================
@app.route("/add-product", methods=["GET", "POST"])
@login_required()
def add_product():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        cursor.execute("""
            INSERT INTO products
            (category, size, type, variant, pattern, quantity, threshold, price, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["category"],
            request.form.get("size"),
            request.form.get("type"),
            request.form.get("variant"),
            request.form.get("pattern"),
            int(request.form["quantity"]),
            int(request.form["threshold"]),
            float(request.form["price"]),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()
        return redirect(url_for("inventory"))

    cursor.execute("SELECT * FROM categories ORDER BY name")
    categories = cursor.fetchall()
    conn.close()

    return render_template("add_product.html", categories=categories)


# =========================
# INVENTORY
# =========================
@app.route("/inventory")
@login_required()
def inventory():
    category = request.args.get("category")

    conn = get_connection()
    cursor = conn.cursor()

    if category:
        cursor.execute("SELECT * FROM products WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT * FROM products")

    products = cursor.fetchall()
    conn.close()

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
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        cursor.execute("""
            UPDATE products
            SET quantity = ?, threshold = ?, price = ?, last_updated = ?
            WHERE id = ?
        """, (
            int(request.form["quantity"]),
            int(request.form["threshold"]),
            float(request.form["price"]),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            product_id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("inventory"))

    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    return render_template("edit_product.html", product=product)


# =========================
# DELETE PRODUCT
# =========================
@app.route("/delete-product/<int:product_id>", methods=["POST"])
@login_required("admin")
def delete_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

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
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        subtotal = 0
        items = []

        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()

        for p in products:
            qty = request.form.get(f"qty_{p[0]}")
            if qty and int(qty) > 0:
                qty = int(qty)
                if qty > p[6]:
                    return "Not enough stock", 400

                # 🔹 Build PRODUCT DESCRIPTION properly
                description_parts = [
                    p[1],        # category
                    p[3],        # type
                    p[2],        # size
                    p[5] or p[4] # pattern OR variant
                ]

                description = " - ".join(
                    [str(x) for x in description_parts if x]
                )

                line_total = qty * p[7]
                subtotal += line_total

                items.append({
                    "product_id": p[0],
                    "description": description,
                    "quantity": qty,
                    "price": p[7],
                    "total": line_total
                })

        # Discount logic
        discount_input = float(request.form["discount"])
        discount = subtotal * discount_input / 100 if discount_input <= 100 else discount_input

        taxable_value = subtotal - discount

        # GST enable / disable
        enable_cgst = "enable_cgst" in request.form
        enable_sgst = "enable_sgst" in request.form

        cgst_percent = float(request.form["cgst_percent"]) if enable_cgst else 0
        sgst_percent = float(request.form["sgst_percent"]) if enable_sgst else 0

        cgst_amount = taxable_value * cgst_percent / 100
        sgst_amount = taxable_value * sgst_percent / 100

        total = taxable_value + cgst_amount + sgst_amount

        # Insert invoice header
        cursor.execute("""
            INSERT INTO invoices
            (customer_name, customer_gstin, subtotal, discount,
             cgst_percent, cgst_amount,
             sgst_percent, sgst_amount,
             taxable_value, total, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["customer_name"],
            request.form["customer_gstin"],
            subtotal,
            discount,
            cgst_percent,
            cgst_amount,
            sgst_percent,
            sgst_amount,
            taxable_value,
            total,
            request.form["invoice_date"] + " " + datetime.now().strftime("%H:%M:%S")
        ))

        invoice_id = cursor.lastrowid

        # Insert invoice items & update stock
        for item in items:
            cursor.execute("""
                INSERT INTO invoice_items
                (invoice_id, product_id, product_name, quantity, price, total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                item["product_id"],
                item["description"],
                item["quantity"],
                item["price"],
                item["total"]
            ))

            cursor.execute("""
                UPDATE products
                SET quantity = quantity - ?
                WHERE id = ?
            """, (item["quantity"], item["product_id"]))

        conn.commit()
        conn.close()

        return redirect(url_for("download_invoice", invoice_id=invoice_id))

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()

    return render_template(
    "create_invoice.html",
    products=products,
    today=datetime.now().strftime("%Y-%m-%d")
)



@app.route("/invoices")
@login_required("admin")
def invoice_history():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            customer_name,
            customer_gstin,
            total,
            created_at
        FROM invoices
        ORDER BY created_at DESC
    """)
    invoices = cursor.fetchall()
    conn.close()

    return render_template("invoice_history.html", invoices=invoices)



@app.route("/download-invoice/<int:invoice_id>")
@login_required("admin")
def download_invoice(invoice_id):
    from utils.invoice_pdf import generate_invoice_pdf
    file_path = generate_invoice_pdf(invoice_id)
    return send_file(file_path, as_attachment=True)



@app.route("/sales-report")
@login_required("admin")
def sales_report():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DATE(created_at), SUM(total)
        FROM invoices
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """)
    daily = cursor.fetchall()

    cursor.execute("""
        SELECT strftime('%Y-%m', created_at), SUM(total)
        FROM invoices
        GROUP BY strftime('%Y-%m', created_at)
        ORDER BY strftime('%Y-%m', created_at)
    """)
    monthly = cursor.fetchall()

    cursor.execute("""
        SELECT SUM(cgst_amount), SUM(sgst_amount)
        FROM invoices
    """)
    gst = cursor.fetchone()

    conn.close()

    return render_template(
        "sales_report.html",
        daily=daily,
        monthly=monthly,
        gst=gst
    )




# =========================
# START APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
