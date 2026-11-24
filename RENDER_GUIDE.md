# Render Deployment Guide

> Deploy your Credit Card Eligibility Prediction project on Render.
> This guide covers: FastAPI backend, frontend, external MySQL, and environment variables.

---

## Architecture on Render

```
Internet → Render Web Service (FastAPI)
              ├── Serves /frontend static files
              ├── API endpoints (/api/*)
              └── Connects to → External MySQL (e.g. PlanetScale / Railway / Aiven)
```

> **Why external MySQL?**
> Render does not provide a managed MySQL service.
> Use one of these free or low-cost external hosts (see Step 3).

---

## Step 1 — Connect GitHub to Render

1. Go to [https://render.com](https://render.com) and sign up / log in.
2. Click **New** → **Web Service**.
3. Under **Connect a repository**, click **Connect GitHub**.
4. Authorize Render to access your GitHub account.
5. Search for and select `credit-eligibility-prediction`.
6. Click **Connect**.

---

## Step 2 — Configure the FastAPI Web Service

Fill in the deployment settings:

| Setting | Value |
|---|---|
| **Name** | `credit-eligibility-api` |
| **Region** | Closest to your users (e.g., Singapore) |
| **Branch** | `main` |
| **Root Directory** | *(leave blank)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free (or Starter for better performance) |

Click **Create Web Service**.

---

## Step 3 — Set Up External MySQL Database

Choose one of these free-tier MySQL providers:

### Option A — PlanetScale (Recommended)
1. Sign up at [https://planetscale.com](https://planetscale.com).
2. Create a new database → name it `credit_risk_db`.
3. Go to **Connect** → select **Connect with: General** → copy the connection string.
4. In your PlanetScale database shell, paste and run the contents of `database/database.sql`.
5. After schema creation, import data by running `import_data.py` locally (pointing `.env` at PlanetScale credentials).

### Option B — Railway
1. Sign up at [https://railway.app](https://railway.app).
2. New Project → **Provision MySQL**.
3. Go to **Variables** to find your MySQL host, port, user, password.
4. Connect your local MySQL client and run `database/database.sql`.

### Option C — Aiven (free 30-day trial)
1. Sign up at [https://aiven.io](https://aiven.io).
2. Create a MySQL service.
3. Use provided credentials.

### Option D — FreeSQLdatabase.com (100% free, 5MB)
- Good for demo/testing only.

---

## Step 4 — Configure Environment Variables on Render

In your Render Web Service dashboard:
1. Click the **Environment** tab.
2. Click **Add Environment Variable** for each:

| Key | Value |
|---|---|
| `DB_HOST` | Your external MySQL hostname |
| `DB_PORT` | `3306` (or as provided) |
| `DB_NAME` | `credit_risk_db` |
| `DB_USER` | Your MySQL username |
| `DB_PASSWORD` | Your MySQL password |
| `MODEL_PATH` | `/opt/render/project/src/model/model_package.joblib` |

3. Click **Save Changes**.

> 💡 Render automatically sets `PORT` — do not override it.

---

## Step 5 — Import Data to External MySQL

After connecting your `.env` to the external database:

```bash
# On your local machine, with .env pointing to external DB:
python backend/import_data.py
```

Confirm:
```
✅ Imported 9000 rows into customers table.
```

---

## Step 6 — Deploy

1. Render auto-deploys when you push to `main`.
2. Watch the **Logs** tab for:
   ```
   ✅ MySQL connection established.
   ✅ Model loaded │ threshold=0.16 │ features=23
   INFO:     Uvicorn running on http://0.0.0.0:XXXX
   ```
3. If you see errors, check environment variables in the **Environment** tab.

---

## Step 7 — Get Your Public URL

1. At the top of your Render service page you will see:
   ```
   https://credit-eligibility-api.onrender.com
   ```
2. Click it — your Bank Officer Dashboard should load.
3. Enter any Customer User ID (e.g., `20174`) and click **CHECK ELIGIBILITY**.

---

## Step 8 — Test from Another Device

Share this URL with any device:
```
https://credit-eligibility-api.onrender.com
```

Test the API directly:
```
https://credit-eligibility-api.onrender.com/api/predict/20174
https://credit-eligibility-api.onrender.com/api/stats
https://credit-eligibility-api.onrender.com/api/docs
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `Database connection failed` | Check DB_HOST, DB_USER, DB_PASSWORD environment variables |
| `Model file not found` | Verify `model/model_package.joblib` is committed to GitHub |
| `Customer not found` | Run `import_data.py` against the production DB |
| `502 Bad Gateway` | Check Render logs; server may be starting up (free tier cold start ~30s) |
| `CORS error` | Already handled in `main.py` with `allow_origins=["*"]` |

---

## Production Checklist

- [ ] External MySQL running and accessible from Render
- [ ] `database.sql` schema applied to production DB
- [ ] 9,000 rows imported via `import_data.py`
- [ ] All 5 environment variables set in Render
- [ ] Model file committed and pushed to GitHub
- [ ] Health check passing: `GET /health`
- [ ] Test prediction: `GET /api/predict/20174`
