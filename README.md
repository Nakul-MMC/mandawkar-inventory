# Mandawkar Inventory Management System

A robust, Flask-based Inventory and Finance management system designed for small businesses. Tracks Stock, Sales, Purchases, Receivables, and Payables with a clean, responsive UI.

## Features

*   **Inventory Management**: Track products, categories, types, patterns, and stock levels.
*   **Billing & Invoicing**: Create GST-compliant invoices with automatic stock deduction.
*   **Finance Dashboard**: Track Customer Receivables and Dealer Payables (Sorted by Pending status).
*   **Stock In**: Record purchases from dealers, update stock, and manage payables in one flow.
*   **History Search**: Instantly find past invoices by Customer Name or Invoice ID.
*   **PDF Generation**: Download professional Invoice PDFs (works in Desktop Mode too).
*   **Excel Export**: Export complete inventory data for analysis.
*   **Desktop App**: Runs as a standalone `.exe` without needing command line.
*   **Audit Logs**: Track every action (Create, Update, Delete) in the system.

---

## Technical Requirements

To run this application, you need:
1.  **Python 3.8 or higher** installed on your computer.
2.  A web browser (Chrome, Edge, Firefox).

---

## Installation & Setup (For New Devices)

Follow these steps to set up the application on a new computer:

### 1. Install Python
If you haven't already, download and install Python from [python.org](https://www.python.org/downloads/).
*   **Important**: During installation, check the box **"Add Python to PATH"**.

### 2. Open the Project Folder
Open a terminal (Command Prompt or PowerShell) and navigate to this folder.

### 3. Install Dependencies
Run the following command to install the required libraries:
```bash
pip install -r requirements.txt
```
*Note: If `pip` is not recognized, try `python -m pip install -r requirements.txt`.*

### 4. Run the Application
Start the application by running:
```bash
python app.py
```

### 5. Access the App
Open your web browser and go to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Default Login

On the first run, the system automatically creates an Admin account:

*   **Username**: `admin`
*   **Password**: `admin123`

*Please change this password or create a new user after logging in for security.*

---

## Data Storage & Backup

*   **Where is my data?**
    All data (Products, Invoices, Customers) is stored in a single file:
    `instance/db.sqlite3`

*   **How to Backup?**
    Simply copy the `instance/db.sqlite3` file to a safe location (like Google Drive or a USB stick).

*   **How to Restore?**
    If you move to a new computer, install the app as per the steps above, then replace the empty `instance/db.sqlite3` with your backup copy.

---

## Troubleshooting

*   **"No module named..." error**: Run existing `pip install -r requirements.txt` again.
*   **Database Locked**: Ensure the app is not open in another window or terminal.
