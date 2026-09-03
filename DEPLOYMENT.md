# LedgerSense Deployment Guide
### Supabase and Netlify Deployment Manual

---

## 1. Deploying to Netlify

Netlify hosts the static interactive dashboard with live charts, search filters, exception inspection drawers, and export actions.

### Option A: Instant Drag and Drop (No Git Required)
1. Go to **[app.netlify.com/drop](https://app.netlify.com/drop)** in your browser.
2. Sign in to your Netlify account.
3. Drag the **`public`** folder from `C:\Users\SAANVI\Desktop\LedgerSense\public` directly into the Netlify drop zone.
4. Your dashboard will be live on an HTTPS URL immediately (e.g., `https://ledgersense-recon.netlify.app`).

### Option B: Deploy via GitHub / Netlify CLI
1. Initialize a git repository and push to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for LedgerSense"
   git branch -M main
   git remote add origin https://github.com/your-username/ledgersense.git
   git push -u origin main
   ```
2. In Netlify, click **"Add new site" -> "Import an existing project"**.
3. Select your GitHub repository. Netlify will automatically detect `netlify.toml` and set the publish directory to `public`.
4. Click **Deploy**.

---

## 2. Deploying to Supabase

Supabase stores the relational financial records, settlements, bank credits, and audit summaries.

### Step 1: Create Database Tables
1. Go to your **[Supabase Dashboard](https://app.supabase.com)** and create a new project.
2. Open the **SQL Editor** from the left navigation panel.
3. Open `supabase/schema.sql` from your LedgerSense folder, paste the SQL contents into the editor, and click **Run**.
4. This provisions 5 relational tables:
   - `internal_orders`
   - `razorpay_settlements`
   - `bank_statements`
   - `reconciliation_records`
   - `audit_summaries`

### Step 2: Sync Data to Supabase
1. Install the Supabase Python SDK:
   ```bash
   pip install supabase
   ```
2. Copy your **Project URL** and **Service Role API Key** from `Project Settings -> API`.
3. Set your environment variables and execute the sync script:
   ```powershell
   $env:SUPABASE_URL = "https://your-project.supabase.co"
   $env:SUPABASE_KEY = "your-service-role-key"
   python supabase/sync_data.py
   ```
4. All 100 internal orders, 95 gateway settlements, 90 bank statement records, and reconciled audit rows will be synchronized to your Supabase PostgreSQL database.

---

## 3. Local Streamlit Dashboard

To run the local Python dashboard:
```bash
streamlit run app.py
```
Open `http://localhost:8501` to view the Python controller dashboard.
