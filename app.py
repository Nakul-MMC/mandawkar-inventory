from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from utils.db import create_tables, get_connection

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

    conn.close()

    return render_template(
        "dashboard.html",
        total_quantity=total_quantity,
        total_value=round(total_value, 2)
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


# ---------------- INVENTORY LIST ----------------
@app.route("/inventory")
def inventory():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    conn.close()

    return render_template("inventory.html", products=products)


if __name__ == "__main__":
    app.run(debug=True)
