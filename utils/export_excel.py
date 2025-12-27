import pandas as pd
from datetime import datetime
from utils.db import get_connection
import os

def export_inventory_to_excel():
    conn = get_connection()
    query = """
        SELECT
            category,
            size,
            type,
            variant,
            pattern,
            quantity,
            price,
            quantity * price AS total_value,
            last_updated
        FROM products
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    df["exported_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not os.path.exists("exports"):
        os.mkdir("exports")

    filename = f"exports/inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(filename, index=False)

    return filename
