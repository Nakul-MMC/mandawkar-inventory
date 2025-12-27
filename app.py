from flask import Flask, render_template
from utils.db import create_tables, get_connection

app = Flask(__name__)

# Create DB tables on app start
create_tables()

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

if __name__ == "__main__":
    app.run(debug=True)
