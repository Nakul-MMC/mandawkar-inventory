from app import app, db, Invoice, InvoiceItem, Product
from utils.invoice_pdf import generate_invoice_pdf
import uuid
from datetime import datetime
import os

def test_invoice_mismatch():
    print("Starting Invoice Mismatch Test...")
    
    with app.app_context():
        # 1. Create a FRESH Unique Product
        unique_sku = f"TestItem_{uuid.uuid4().hex[:6]}"
        p = Product(
            category="TestCat", size="10x10", type="TestType", 
            variant=unique_sku, pattern="Pattern", 
            quantity=100, price=50.0, 
            last_updated=datetime.now().strftime("%Y-%m-%d")
        )
        db.session.add(p)
        db.session.commit()
        print(f"Created Product: {p.id} - {unique_sku}")

        # 2. Create Invoice for "N Test 2"
        inv_number = f"INV-{uuid.uuid4().hex[:8]}"
        customer_name = "N Test 2"
        qty_bought = 1
        
        inv = Invoice(
            invoice_number=inv_number,
            customer_name=customer_name, # Critical: Check if this saves as "N Test 2"
            customer_gstin="UniqueGSTIN",
            subtotal=50.0, discount=0, cgst_percent=0, cgst_amount=0, sgst_percent=0, sgst_amount=0,
            taxable_value=50.0, total=50.0,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_active=True
        )
        db.session.add(inv)
        db.session.flush()
        
        item = InvoiceItem(
            invoice_id=inv.id,
            product_id=p.id,
            product_name=f"TestCat - {unique_sku}", # Critical: Check description
            quantity=qty_bought,
            price=50.0,
            total=50.0
        )
        db.session.add(item)
        db.session.commit()
        
        print(f"Created Invoice ID: {inv.id} for Customer: {inv.customer_name}")
        
        # 3. Verify DB Data
        # Re-fetch to be sure
        inv_check = Invoice.query.get(inv.id)
        print(f"DB Verification -> ID: {inv_check.id}, Customer: {inv_check.customer_name} (Expected: 'N Test 2')")
        
        item_check = InvoiceItem.query.filter_by(invoice_id=inv.id).first()
        print(f"DB Verification -> Item: {item_check.product_name}, Qty: {item_check.quantity} (Expected: 1)")
        
        if inv_check.customer_name != "N Test 2":
            print("CRITICAL FAILURE: DB saved wrong name!")
            return

        if item_check.quantity != 1:
            print("CRITICAL FAILURE: DB saved wrong quantity!")
            return
            
        # 4. Generate PDF
        print(f"Generating PDF for Invoice ID: {inv.id}...")
        pdf_path = generate_invoice_pdf(inv.id)
        print(f"PDF generated at: {pdf_path}")
        
        # 5. "Blind" verification (since we can't OCR easily)
        # We rely on the fact that generate_invoice_pdf fetches by ID.
        # If DB is correct, PDF *should* be correct unless generate_invoice_pdf has hardcoded ID.
        # Let's inspect generate_invoice_pdf source code text again to be paranoid about hardcoded values.
        
        import inspect
        from utils import invoice_pdf
        src = inspect.getsource(invoice_pdf.generate_invoice_pdf)
        if "Nakul" in src:
            print("CRITICAL WARNING: Found 'Nakul' hardcoded in invoice_pdf.py!")
        if "Chemical" in src:
            print("CRITICAL WARNING: Found 'Chemical' hardcoded in invoice_pdf.py!")
            
        print("Test Complete. Please manually check the PDF path above if script passes.")

if __name__ == "__main__":
    test_invoice_mismatch()
