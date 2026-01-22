import pandas as pd
from datetime import datetime
from models import db # Import shared db instance
import os

def export_inventory_to_excel():
    # Use SQLAlchemy Engine directly
    query = """
        SELECT
            category,
            size,
            type,
            variant,
            pattern,
            quantity,
            price,
            (quantity * price) AS total_value
        FROM products
    """
    df = pd.read_sql_query(query, db.engine.connect()) # .connect() for SQLAlchemy 2.0 safety

    df["exported_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    import sys
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.getcwd()
        
    output_dir = os.path.join(base_dir, "exports")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filepath = os.path.join(output_dir, f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    df.to_excel(filepath, index=False)
    
    return filepath
