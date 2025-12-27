import sqlite3
from werkzeug.security import generate_password_hash

DB_NAME = "db.sqlite3"


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # =========================
    # PRODUCTS
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            size TEXT,
            type TEXT,
            variant TEXT,
            pattern TEXT,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            last_updated TEXT NOT NULL
        )
    """)

    # =========================
    # CATEGORIES
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.executemany("""
        INSERT OR IGNORE INTO categories (name)
        VALUES (?)
    """, [
        ("Tiles",),
        ("Granite",),
        ("Kadappa",),
        ("Chemicals",)
    ])

    # =========================
    # USERS
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # Default admin user
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES (?, ?, ?)
    """, (
        "admin",
        generate_password_hash("admin123"),
        "admin"
    ))

    # =========================
    # INVOICES (HEADER)
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_gstin TEXT,

            subtotal REAL,
            discount REAL,

            cgst_percent REAL,
            cgst_amount REAL,

            sgst_percent REAL,
            sgst_amount REAL,

            taxable_value REAL,
            total REAL,

            created_at TEXT
        )
    """)

    # =========================
    # INVOICE ITEMS (LINE ITEMS)
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            product_id INTEGER,
            product_name TEXT,
            quantity INTEGER,
            price REAL,
            total REAL
        )
    """)

    conn.commit()
    conn.close()
