from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
import sqlite3
import os

DB_NAME = os.path.join(os.getcwd(), "instance", "db.sqlite3")

def generate_invoice_pdf(invoice_id):
    if not os.path.exists("invoices"):
        os.mkdir("invoices")

    filename = f"invoices/invoice_{invoice_id}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']
    
    # ---------------- DATA FETCHING ----------------
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Invoice Header
    cursor.execute("""
        SELECT
            id, invoice_number, customer_name, customer_gstin,
            subtotal, discount, cgst_percent, cgst_amount,
            sgst_percent, sgst_amount, taxable_value, total, created_at
        FROM invoices
        WHERE id = ?
    """, (invoice_id,))
    inv = cursor.fetchone()
    
    # Invoice Items
    cursor.execute("""
        SELECT product_name, quantity, price, total
        FROM invoice_items
        WHERE invoice_id = ?
    """, (invoice_id,))
    items_data = cursor.fetchall()
    
    conn.close()

    if not inv:
        return None

    # ---------------- HEADER SECTION ----------------
    # Simple clear header
    elements.append(Paragraph("MANDAWKAR TRADERS", title_style))
    elements.append(Paragraph("Chimur<br/>GSTIN: 27AKCPM4510DIZN<br/>Contact: 9423601097 / 8669267662", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # ---------------- INVOICE META ----------------
    # (Invoice No, Date, Customer, GSTIN)
    # Using a 2x2 grid for alignment
    meta_data = [
        [f"Invoice No: {inv[1]}", f"Date: {inv[12][:10]}"],
        [f"Customer: {inv[2]}", f"GSTIN: {inv[3] or '-'}"]
    ]
    meta_table = Table(meta_data, colWidths=[4*inch, 2.5*inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.2*inch))

    # ---------------- ITEMS TABLE ----------------
    # Headers
    data = [['Product', 'Qty', 'Rate', 'Amount']]
    
    for item in items_data:
        data.append([
            Paragraph(item[0], normal_style),  # Wrap Name
            str(item[1]),
            f"{item[2]:.2f}",
            f"{item[3]:.2f}"
        ])
    
    # ---------------- TOTALS ----------------
    # We will append totals to the same table to keep alignment perfect
    # Structure: [Empty, Empty, Label, Value]
    
    data.append(['', '', 'Subtotal:', f"{inv[4]:.2f}"])
    data.append(['', '', 'Discount:', f"-{inv[5]:.2f}"])
    data.append(['', '', 'Taxable Value:', f"{inv[10]:.2f}"])
    
    # CGST (Always show row, even if 0, to be explicit)
    cgst_label = f"CGST ({inv[6]}%):" if inv[6] else "CGST:"
    data.append(['', '', cgst_label, f"{inv[7]:.2f}"])
    
    # SGST (Always show row)
    sgst_label = f"SGST ({inv[8]}%):" if inv[8] else "SGST:"
    data.append(['', '', sgst_label, f"{inv[9]:.2f}"])
    
    # GRAND TOTAL
    data.append(['', '', 'TOTAL:', f"{inv[11]:.2f}"])

    # TABLE STYLING
    # Widths: Prod(3.2), Qty(0.8), Rate(1.0), Amt(1.5) -> Total 6.5 inch
    t_items = Table(data, colWidths=[3.2*inch, 0.8*inch, 1.0*inch, 1.5*inch])
    
    # Calculate row indices
    last_item_row = len(items_data) # Header is 0, Items are 1 to len
    total_row = len(data) - 1
    
    style = [
        # HEADER STYLE
        ('BACKGROUND', (0,0), (-1,0), colors.Color(0.9, 0.9, 0.9)),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('ALIGN', (1,0), (-1,0), 'CENTER'), # Qty Header Center
        ('ALIGN', (2,0), (-1,0), 'RIGHT'), # Rate Header Right
        ('ALIGN', (3,0), (-1,0), 'RIGHT'), # Amt Header Right
        ('PADDING', (0,0), (-1,0), 6),
        
        # ITEM STYLE
        ('VALIGN', (0,1), (-1, last_item_row), 'TOP'),
        ('ALIGN', (1,1), (1, last_item_row), 'CENTER'), # Qty Center
        ('ALIGN', (2,1), (-1, last_item_row), 'RIGHT'), # Rate/Amt Right
        ('GRID', (0,0), (-1, last_item_row), 0.5, colors.grey), # Grid for items only
        
        # TOTALS STYLE
        ('ALIGN', (-2, last_item_row+1), (-1, -1), 'RIGHT'), # All total labels/values Right
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'), # Grand Total Bold
        ('FONTSIZE', (-2, -1), (-1, -1), 12),
        ('TOPPADDING', (-2, -1), (-1, -1), 10),
        ('LINEABOVE', (-2, -1), (-1, -1), 1, colors.black), # Line above Total
    ]
    
    t_items.setStyle(TableStyle(style))
    elements.append(t_items)
    
    # Build
    doc.build(elements)
    return filename
