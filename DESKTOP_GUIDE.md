# How to Create the Desktop App (.exe)

Follow these steps to convert this project into a standalone Windows Application (like MS Word or Excel) that you can share with your friend.

## Prerequisites
Ensure Python is installed on your computer.

## Step 1: Build the App
1.  Open the project folder.
2.  Double-click on the file **`build_exe.bat`**.
3.  A black window will appear. It will:
    *   Install the packaging tools.
    *   Bundle all the code, templates, and libraries.
    *   Create the `.exe` file.
4.  Wait for it to say **"BUILD COMPLETE!"**.

## Step 2: Locate the App
1.  Once the build finishes, you will see a new folder named **`dist`**.
2.  Open it. Inside, you will find **`Inventory Manager.exe`**.

## Step 3: Deployment (Sharing)
1.  You can copy **`Inventory Manager.exe`** to your friend's computer.
2.  **Important**: When you run the app for the first time on a new computer, it will create a **`data`** folder next to it.
    *   This `data` folder is where the database (`db.sqlite3`) will be stored.
    *   If you want to move the app, move the `.exe` AND the `data` folder together to keep the records.

## Usage
Simply double-click **`Inventory Manager.exe`**.
*   It will automatically open your web browser to the Login Page.
*   Login with `admin` / `admin123`.
*   When you are done, you can close the black console window (if visible) or just close the browser.

## How to Update the App (Without Data Loss)
If you (the developer) make changes to the code to fix bugs or add features:

### 1. Developer Side
1.  Make your code changes.
2.  Double-click **`build_exe.bat`** again.
3.  This creates a **new** `Inventory Manager.exe` in the `dist` folder.
4.  Send this **new file** to your friend.

### 2. User Side (Your Friend)
1.  **Stop** the current app if it's running.
2.  **Delete** (or rename) the old `Inventory Manager.exe`.
3.  **Paste** the new `Inventory Manager.exe` in the **same folder**.
4.  **Do NOT touch the `data` folder**.
    *   The `data` folder contains `db.sqlite3` (all their customers, bills, etc.).
    *   As long as the `data` folder stays next to the `.exe`, the new app will automatically pick up all the existing data.
5.  Run the new `.exe`. It will open with the new features but keep all the old data!
