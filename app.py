from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from utils.db import create_tables, get_connection
from utils.export_excel import export_inventory_to_excel

app = Flask(__name__)

# Initialize DB tables
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


# ---------------- CATEGORIES ----------------
@app.route("/categories", methods=["GET", "POST"])
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


# ---------------- ADD PRODUCT ----------------
@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        cursor.execute("""
            INSERT INTO products
            (category, size, type, variant, pattern, quantity, price, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["category"],
            request.form.get("size"),
            request.form.get("type"),
            request.form.get("variant"),
            request.form.get("pattern"),
            int(request.form["quantity"]),
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

    return render_template(
        "inventory.html",
        products=products,
        selected_category=category
    )


# ---------------- EDIT PRODUCT ----------------
@app.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        cursor.execute("""
            UPDATE products
            SET quantity = ?, price = ?, last_updated = ?
            WHERE id = ?
        """, (
            int(request.form["quantity"]),
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


# ---------------- DELETE PRODUCT (FIX) ----------------
@app.route("/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("inventory"))


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
