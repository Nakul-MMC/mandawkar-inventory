from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
import sqlite3
import os

DB_NAME = "db.sqlite3"

def generate_invoice_pdf(invoice_id):
    if not os.path.exists("invoices"):
        os.mkdir("invoices")

    filename = f"invoices/invoice_{invoice_id}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
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
    company_name = Paragraph("MANDAWKAR TRADERS", title_style)
    address = Paragraph("Chimur<br/>GSTIN: 27AKCPM4510DIZN<br/>Contact: 9423601097 / 8669267662", normal_style)
    
    elements.append(company_name)
    elements.append(address)
    elements.append(Spacer(1, 0.2*inch))
    
    # ---------------- INVOICE DETAILS ----------------
    # Grid for Invoice Info and Customer Info
    inv_info = [
        [f"Invoice No: {inv[1]}", f"Date: {inv[12][:10]}"],
        [f"Customer: {inv[2]}", f"GSTIN: {inv[3] or '-'}"]
    ]
    t_info = Table(inv_info, colWidths=[3.5*inch, 2.5*inch])
    t_info.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 0.2*inch))

    # ---------------- ITEMS TABLE ----------------
    # ---------------- ITEMS TABLE ----------------
    # Headers
    data = [['Product', 'Qty', 'Rate (Rs)', 'Amount (Rs)']]
    
    # Rows
    item_count = 0
    for item in items_data:
        data.append([
            Paragraph(item[0], normal_style),  # Wrap long names
            str(item[1]),      # Qty
            f"{item[2]:.2f}",  # Rate
            f"{item[3]:.2f}"   # Amount
        ])
        item_count += 1
    
    # Totals Section (Added as rows)
    data.append(['', '', 'Subtotal:', f"{inv[4]:.2f}"])
    
    extra_rows = 1 # Subtotal
    
    if inv[5] > 0:
        data.append(['', '', 'Discount:', f"-{inv[5]:.2f}"])
        extra_rows += 1
        
    data.append(['', '', 'Taxable Value:', f"{inv[10]:.2f}"])
    extra_rows += 1
    
    if inv[7] > 0:
        data.append(['', '', f"CGST ({inv[6]}%):", f"{inv[7]:.2f}"])
        extra_rows += 1
        
    if inv[9] > 0:
        data.append(['', '', f"SGST ({inv[8]}%):", f"{inv[9]:.2f}"])
        extra_rows += 1
        
    data.append(['', '', 'TOTAL:', f"{inv[11]:.2f}"])
    extra_rows += 1

    # Table Styling
    # Safer Widths: 2.7 + 0.8 + 1.0 + 1.2 = 5.7 inch (safe for A4)
    table = Table(data, colWidths=[3.2*inch, 0.7*inch, 1.0*inch, 1.3*inch])
    
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.2, 0.2)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),               # Default left
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),              # Qty, Rate, Amount right aligned
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, item_count), 1, colors.black), # Grid only for items (0 to item_count)
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        
        # Totals styling
        ('LINEABOVE', (-2, -extra_rows), (-1, -extra_rows), 1, colors.black), # Line above Subtotal
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (-2, -1), (-1, -1), 12),
        ('TOPPADDING', (-2, -1), (-1, -1), 12),
    ]
    
    table.setStyle(TableStyle(style_cmds))
    elements.append(table)
    
    # ---------------- BUILD PDF ----------------
    doc.build(elements)
    return filename
