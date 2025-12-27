from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import sqlite3
import os

DB_NAME = "db.sqlite3"


def generate_invoice_pdf(invoice_id):
    if not os.path.exists("invoices"):
        os.mkdir("invoices")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch invoice header
    cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    invoice = cursor.fetchone()

    # Fetch invoice items
    cursor.execute("""
        SELECT product_name, quantity, price, total
        FROM invoice_items
        WHERE invoice_id = ?
    """, (invoice_id,))
    items = cursor.fetchall()

    conn.close()

    filename = f"invoices/invoice_{invoice_id}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)

    # ---------------- HEADER ----------------
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, 800, "MANDAWKAR TRADERS")

    c.setFont("Helvetica", 10)
    c.drawString(40, 785, "Chimur")
    c.drawString(40, 770, "GSTIN: 27AKCPM4510DIZN")
    c.drawString(40, 755, "Contact: 9423601097 / 8669267662")

    c.line(40, 745, 550, 745)

    # ---------------- INVOICE INFO ----------------
    c.drawString(40, 725, f"Invoice No: {invoice_id}")
    c.drawString(350, 725, f"Date: {invoice[-1][:10]}")

    c.drawString(40, 705, f"Customer Name: {invoice[1]}")
    c.drawString(40, 690, f"Customer GSTIN: {invoice[2] or '-'}")

    # ---------------- ITEMS TABLE ----------------
    y = 650
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Product")
    c.drawString(250, y, "Qty")
    c.drawString(300, y, "Rate")
    c.drawString(380, y, "Amount")

    c.line(40, y - 5, 550, y - 5)
    y -= 20

    c.setFont("Helvetica", 10)
    for item in items:
        c.drawString(40, y, item[0])
        c.drawRightString(280, y, str(item[1]))
        c.drawRightString(350, y, f"{item[2]:.2f}")
        c.drawRightString(500, y, f"{item[3]:.2f}")
        y -= 18

        if y < 200:
            c.showPage()
            y = 750

    # ---------------- TOTALS ----------------
    y -= 20
    c.line(300, y, 550, y)
    y -= 20

    c.drawRightString(450, y, "Subtotal:")
    c.drawRightString(550, y, f"{invoice[3]:.2f}")

    y -= 18
    c.drawRightString(450, y, "Discount:")
    c.drawRightString(550, y, f"{invoice[4]:.2f}")

    y -= 18
    c.drawRightString(450, y, "Taxable Value:")
    c.drawRightString(550, y, f"{invoice[9]:.2f}")

    # CGST (only if > 0)
    if invoice[5] and invoice[5] > 0:
        y -= 18
        c.drawRightString(450, y, f"CGST ({invoice[5]}%):")
        c.drawRightString(550, y, f"{invoice[6]:.2f}")

    # SGST (only if > 0)
    if invoice[7] and invoice[7] > 0:
        y -= 18
        c.drawRightString(450, y, f"SGST ({invoice[7]}%):")
        c.drawRightString(550, y, f"{invoice[8]:.2f}")

    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawRightString(450, y, "TOTAL AMOUNT:")
    c.drawRightString(550, y, f"{invoice[10]:.2f}")

    c.showPage()
    c.save()

    return filename
