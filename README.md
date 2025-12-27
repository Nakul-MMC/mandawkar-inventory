# 🏪 Mandawkar Traders – Inventory & Billing System

A **complete Inventory, Billing, and Sales Management System** built for a tile, granite, kadappa, and sanitary shop.

This application supports **product-wise stock management, GST billing with PDF invoices, sales reports with charts, and low stock alerts**, designed for real-world shop usage.

---

## ✨ Features

### 📦 Inventory Management
- Add / edit / delete products
- Category, size, type, pattern / variant support
- Product-wise low stock threshold
- Red highlight for low stock items

### 📊 Dashboard
- Total stock quantity
- Total inventory value
- Inventory-level stock summary
- Low stock alert badge

### 🧾 GST Billing
- Generate GST invoices with:
  - CGST / SGST enable-disable
  - Adjustable tax percentages
  - Discount (% or ₹)
- Product-based billing (auto stock reduction)
- Backdated invoice support
- Professional PDF invoices with shop details

### 🗂 Invoice History
- View all invoices
- Reprint / download invoice PDFs anytime

### 📈 Sales Reports
- Daily sales report
- Monthly sales report
- Interactive charts (Chart.js)
- Total GST collected summary

### 🔐 Authentication
- Login system
- Admin / Staff roles
- Secure access to billing & deletion features

---

## 🛠 Tech Stack

- **Backend:** Python (Flask)
- **Frontend:** HTML, Bootstrap, Jinja2
- **Database:** SQLite (local)
- **PDF Generation:** ReportLab
- **Charts:** Chart.js
- **Version Control:** Git & GitHub

---

## 🚀 How to Run Locally (Step-by-Step)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Nakul-MMC/mandawkar-inventory.git
cd mandawkar-inventory


## ▶ How to Run
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py

http://127.0.0.1:5000

Username: admin
Password: admin123
```
### Project Structure (Simplified)
mandawkar-inventory/
│
├── app.py
├── db.sqlite3
├── requirements.txt
├── README.md
│
├── templates/
│   ├── dashboard.html
│   ├── inventory.html
│   ├── create_invoice.html
│   ├── invoice_history.html
│   ├── sales_report.html
│   └── base.html
│
├── static/
│   ├── css/
│   └── images/
│
├── utils/
│   ├── db.py
│   ├── export_excel.py
│   └── invoice_pdf.py
│
└── invoices/


