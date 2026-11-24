# Complete Deployment Guide

> End-to-end reference: local development → GitHub → Render production.

---

## 1. Local Development Setup

### 1.1 Requirements
- Python 3.11+
- MySQL 8.x (local)
- Git
- pip

### 1.2 Install Python dependencies
```bash
cd credit_eligibility_project
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Mac/Linux
pip install -r requirements.txt
```

### 1.3 Environment configuration
```bash
cp .env.example .env
# Open .env and set DB_PASSWORD to your local MySQL root password
```

### 1.4 Database setup
```bash
# Create schema
mysql -u root -p < database/database.sql

# Import 9000 customer rows
python backend/import_data.py
```

### 1.5 Run the server
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 1.6 Verify
- Dashboard: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Health: http://localhost:8000/health
- Test: http://localhost:8000/api/predict/20174

---

## 2. Database Relationships

```
customers (user_id PK)
    │
    └── prediction_history (user_id FK → customers.user_id)
```

| Table | Purpose |
|---|---|
| `customers` | 9,000 UCI dataset records; source of truth for customer lookup |
| `prediction_history` | Audit log of every eligibility check by the bank officer |

---

## 3. ML Model Pipeline

```
Customer User ID
    ↓ MySQL lookup
Customer row (25 columns)
    ↓ Drop ID + target column
23 feature DataFrame
    ↓ ColumnTransformer (StandardScaler for numeric, passthrough for categorical)
    ↓ RandomForestClassifier (200 trees, balanced weights)
P(default), P(no-default)
    ↓ Threshold: 0.16
Credit Card Status (APPROVED / NOT APPROVED)
    ↓
Estimated Credit Health Score = round(100 × (1 − P(default)))
    ↓
Store in prediction_history
    ↓
Return JSON → Frontend renders dashboard
```

---

## 4. API Reference

### GET `/health`
Returns server and DB status.
```json
{"status":"ok","model_loaded":true,"db_connected":true}
```

### GET `/api/predict/{user_id}`
Returns full prediction result.
```json
{
  "user_id": 20174,
  "limit_bal": 150000,
  "age": 49,
  "education": "University",
  "default_probability": 0.4352,
  "credit_health_score": 56,
  "credit_card_status": "NOT APPROVED",
  ...
}
```

### GET `/api/history/{user_id}?limit=10`
Returns last 10 prediction records for the customer.

### GET `/api/stats`
Returns dashboard-level statistics.

### GET `/api/docs`
Swagger UI — interactive API documentation.

---

## 5. GitHub → Render CI/CD Flow

```
Local edit → git commit → git push origin main
                                    ↓
                          GitHub triggers Render webhook
                                    ↓
                          Render pulls latest code
                                    ↓
                          pip install -r requirements.txt
                                    ↓
                          uvicorn backend.main:app --host 0.0.0.0 --port $PORT
                                    ↓
                          Live at https://your-app.onrender.com
```

---

## 6. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DB_HOST` | ✅ | MySQL hostname |
| `DB_PORT` | ✅ | MySQL port (default 3306) |
| `DB_NAME` | ✅ | Database name (credit_risk_db) |
| `DB_USER` | ✅ | MySQL username |
| `DB_PASSWORD` | ✅ | MySQL password (never hardcode) |
| `MODEL_PATH` | Optional | Absolute path to model_package.joblib |

---

## 7. Project File Map

```
credit_eligibility_project/
├── backend/
│   ├── main.py           ← All FastAPI routes, model loading, DB logic
│   └── import_data.py    ← One-time CSV importer
├── frontend/
│   ├── index.html        ← Single-page Bank Officer Dashboard
│   ├── style.css         ← Dark theme, responsive layout
│   └── app.js            ← API calls, result rendering, clock
├── model/
│   └── model_package.joblib   ← {model, threshold, feature_names}
├── database/
│   ├── database.sql           ← CREATE TABLE statements
│   └── credit_card_default_under_1mb.csv
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

## 8. Frequently Asked Questions

**Q: Can I use a different database?**
A: The backend uses SQLAlchemy, so you can swap MySQL for PostgreSQL by changing the connection string prefix to `postgresql+psycopg2://` and updating `requirements.txt`.

**Q: Why is the threshold 0.16?**
A: It was optimized during training using a cost matrix where missing a default (false negative) costs 10× more than rejecting a good applicant (false positive).

**Q: Why is the Credit Health Score not a CIBIL score?**
A: CIBIL scores are computed by credit bureaus using proprietary data. Our score is a simple, transparent transformation of the model's default probability for illustrative purposes only.

**Q: Does the app work if MySQL is down?**
A: The `/health` endpoint reports `db_connected: false`. All `/api/predict/*` calls return HTTP 503 with a clear error message.

**Q: How do I update the dataset?**
A: Replace `database/credit_card_default_under_1mb.csv` and re-run `python backend/import_data.py`. The script truncates and re-inserts all rows.
