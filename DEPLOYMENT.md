# Deploying to the Cloud (Render.com)

This guide will help you deploy your Flask Inventory App to the web so you can access it from anywhere. We will use **Render.com** because it offers a very simple setup and has a generous free tier for getting started.

## Step 1: Create a GitHub Repository
1.  Go to [GitHub.com](https://github.com/) and sign in.
2.  Create a **New Repository**. Name it `mandawkar-inventory`.
3.  Make sure it is **Private** (so your data stays safe).
4.  **Upload your project code**:
    *   If using Git on your computer:
        ```bash
        git init
        git add .
        git commit -m "Initial commit"
        git branch -M main
        git remote add origin https://github.com/YOUR_USERNAME/mandawkar-inventory.git
        git push -u origin main
        ```
    *   *Alternatively*, you can upload files manually via the "Upload files" button on GitHub (but Git is recommended).

## Step 2: Create a Render Account
1.  Go to [Render.com](https://render.com/).
2.  Click **Get Started**.
3.  Sign up using your **GitHub** account (this makes connecting easier).

## Step 3: Create a PostgreSQL Database
To ensure your data is safe and permanent, we need a database.
1.  In the Render Dashboard, click **New +** and select **PostgreSQL**.
2.  **Name**: `inventory-db`
3.  **Region**: Choose a region close to you (e.g., Singapore or Frankfurt).
4.  **Instance Type**: Select **Free**.
5.  Click **Create Database**.
6.  **Wait**: It will take a minute or two to create.
7.  Once created, find the **"Internal Database URL"** section. Keep this tab open.

## Step 4: Create a Web Service
1.  Go back to the Render Dashboard.
2.  Click **New +** and select **Web Service**.
3.  Connect your GitHub repository (`mandawkar-inventory`).
4.  **Name**: `inventory-app` (or any unique name).
5.  **Region**: Same as your database.
6.  **Branch**: `main`.
7.  **Runtime**: Python 3.
8.  **Build Command**: `pip install -r requirements.txt` (Render should auto-detect this).
9.  **Start Command**: `gunicorn app:app` (Render should auto-detect this from your Procfile).
10. **Instance Type**: Select **Free**.

## Step 5: Connect Database to App
1.  Scroll down to the **Environment Variables** section on the Web Service creation page.
2.  Click **Add Environment Variable**.
3.  **Key**: `DATABASE_URL`
4.  **Value**: Paste the **"Internal Database URL"** you copied from the Database page in Step 3.
5.  Click **Create Web Service**.

## Step 6: Deployment
Render will now start building your app.
1.  Click on the **Logs** tab to watch the progress.
2.  It will install dependencies and start the Gunicorn server.
3.  Once you see "Your service is live", click the URL at the top (e.g., `https://inventory-app.onrender.com`).

**Success!** Your app is now live.

## Important Notes on Free Tier
*   **Spin Down**: On the free tier, your Web Service will go to sleep if not used for 15 minutes. The next time you visit, it might take **30-60 seconds to load**. This is normal for free plans.
*   **Database**: Render's free PostgreSQL database expires after 90 days. You should backup your data or upgrade to a paid plan ($7/month) for permanent production use.

## Admin Access
When deployed, you will need to log in. The default credentials are:
*   **User**: `admin`
*   **Pass**: `admin123`
*(Change this immediately after logging in)*
