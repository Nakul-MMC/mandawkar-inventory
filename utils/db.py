import sqlite3
from datetime import datetime

DB_NAME = "db.sqlite3"

def get_connection():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

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

    conn.commit()
    conn.close()
