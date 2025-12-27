import sqlite3

DB_NAME = "db.sqlite3"

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Products table
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

    # Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Insert default categories (only once)
    cursor.executemany("""
        INSERT OR IGNORE INTO categories (name)
        VALUES (?)
    """, [
        ("Tiles",),
        ("Granite",),
        ("Kadappa",),
        ("Chemicals",)
    ])

    conn.commit()
    conn.close()
