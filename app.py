from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from utils.db import create_tables, get_connection
from utils.export_excel import export_inventory_to_excel

app = Flask(__name__)

# Create DB tables on startup
create_tables()


# ---------------- DASHBOARD ----------------
@app.route("/")
def dashboard():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(quantity) FROM products")
    total_quantity = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(quantity * price) FROM products")
    total_value = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT category, SUM(quantity), SUM(quantity * price)
        FROM products
        GROUP BY category
    """)
    summary = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total_quantity=total_quantity,
        total_value=round(total_value, 2),
        summary=summary
    )


# ---------------- ADD PRODUCT ----------------
@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        category = request.form["category"]
        size = request.form.get("size")
        type_ = request.form.get("type")
        variant = request.form.get("variant")
        pattern = request.form.get("pattern")
        quantity = int(request.form["quantity"])
        price = float(request.form["price"])

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO products
            (category, size, type, variant, pattern, quantity, price, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            category,
            size,
            type_,
            variant,
            pattern,
            quantity,
            price,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("inventory"))

    return render_template("add_product.html")


# ---------------- INVENTORY ----------------
@app.route("/inventory")
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

    return render_template("inventory.html", products=products, selected_category=category)


# ---------------- EDIT PRODUCT ----------------
@app.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        quantity = int(request.form["quantity"])
        price = float(request.form["price"])

        cursor.execute("""
            UPDATE products
            SET quantity = ?, price = ?, last_updated = ?
            WHERE id = ?
        """, (
            quantity,
            price,
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


# ---------------- EXPORT ----------------
@app.route("/export")
def export():
    filename = export_inventory_to_excel()
    return f"""
        <h3>Export Successful</h3>
        <p>File saved at:</p>
        <b>{filename}</b><br><br>
        <a href="/inventory">Back to Inventory</a>
    """


if __name__ == "__main__":
    app.run(debug=True)
