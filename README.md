# Credit Card Eligibility Prediction

> **ML-powered credit eligibility decision-support dashboard for bank officers.**
> Built with FastAPI · MySQL · Random Forest · Vanilla JS

---

## 📸 Overview

A bank officer enters a **Customer User ID** and immediately receives:

| Feature | Description |
|---|---|
| **Customer Profile** | Credit limit, age, education, marital status |
| **Payment History** | 6-month repayment status, bill amounts, payment amounts |
| **ML Prediction** | Default / no-default probability from trained Random Forest |
| **Credit Card Status** | ✅ APPROVED or ❌ NOT APPROVED |
| **Estimated Credit Health Score** | 0–100 model-based indicator (not a CIBIL score) |
| **Prediction History** | All past checks for this customer |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **ML Model** | Random Forest Classifier (scikit-learn 1.5) |
| **Backend** | FastAPI + Uvicorn (Python 3.11+) |
| **Database** | MySQL 8.x |
| **ORM** | SQLAlchemy 2.0 |
| **Frontend** | HTML5 · CSS3 · Vanilla JavaScript (no framework) |
| **Deployment** | Render (backend) + External MySQL host |

---

## 📁 Project Structure

```
credit_eligibility_project/
│
├── backend/
│   ├── main.py           ← FastAPI application (all endpoints)
│   └── import_data.py    ← One-time CSV → MySQL importer
│
├── frontend/
│   ├── index.html        ← Bank Officer Dashboard
│   ├── style.css         ← Dark banking theme
│   └── app.js            ← Fetch API calls + result rendering
│
├── model/
│   └── model_package.joblib   ← Trained Random Forest + threshold + features
│
├── database/
│   ├── database.sql           ← MySQL schema (create tables)
│   └── credit_card_default_under_1mb.csv   ← Source dataset (9000 rows)
│
├── requirements.txt
├── .env.example
├── .gitignore
├── render.yaml
├── README.md
├── GITHUB_GUIDE.md
├── RENDER_GUIDE.md
└── DEPLOYMENT_GUIDE.md
```

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11 or higher
- MySQL 8.x running locally
- pip

### Step 1 — Clone / Extract
```bash
# If you have a ZIP, extract it first, then:
cd credit_eligibility_project
```

### Step 2 — Create virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac / Linux
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment variables
```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

### Step 5 — Create database schema
```bash
mysql -u root -p < database/database.sql
```

### Step 6 — Import CSV dataset
```bash
python backend/import_data.py
```
Expected output:
```
✅ Database connection OK.
✅ Imported 9000 rows into customers table.
```

### Step 7 — Start the FastAPI server
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 8 — Open in browser
```
http://localhost:8000
```

Or open `frontend/index.html` directly in your browser (the JS auto-detects localhost).

---

## 🔌 API Endpoints

| Method | URL | Description |
|---|---|---|
| GET | `/health` | Server + DB health check |
| GET | `/api/predict/{user_id}` | Run prediction for a customer |
| GET | `/api/history/{user_id}` | Last 10 predictions for customer |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/docs` | Swagger UI (auto-generated) |
| GET | `/api/redoc` | ReDoc documentation |

---

## 🤖 ML Model Details

| Property | Value |
|---|---|
| Algorithm | Random Forest Classifier |
| Preprocessing | StandardScaler (numeric) + Passthrough (categorical) |
| Hyperparameters | n_estimators=200, max_depth=12, min_samples_split=5, min_samples_leaf=4 |
| Class weight | balanced |
| Decision threshold | **0.16** (cost-sensitive: cost_fn=500, cost_fp=50) |
| ROC-AUC | 0.7687 |
| Input features | 23 (excludes ID and target) |

**Decision logic:**

```
if P(default) < 0.16  →  APPROVED
if P(default) ≥ 0.16  →  NOT APPROVED
```

---

## 📊 Estimated Credit Health Score

```
Score = round(100 × (1 − P(default)))
```

| Score Range | Category |
|---|---|
| 80–100 | Excellent |
| 60–79  | Good |
| 40–59  | Fair |
| 20–39  | Poor |
| 0–19   | Very Poor |

> ⚠️ **This score is an illustrative, model-derived indicator only.**
> It is NOT a CIBIL score or any official credit bureau rating.

---

## 🗄️ Database Schema

**Table: `customers`**
- Stores all 9,000 customer records from the UCI dataset.
- Primary key: `user_id` (original `ID` column).

**Table: `prediction_history`**
- Stores every eligibility check performed.
- Foreign key → `customers.user_id`.
- Columns: `default_probability`, `no_default_probability`, `estimated_credit_score`, `credit_card_status`, `prediction_date`.

---

## 🔐 Security

- Never commit your real `.env` file.
- Database credentials are always loaded from environment variables.
- The `.gitignore` excludes `.env`.

---

## 📜 Disclaimer

This application is a **decision-support tool** for internal bank officer use only.
Predictions are model-based recommendations and do **not** constitute legally binding credit approvals.
The Estimated Credit Health Score is **not** an official credit bureau score.
