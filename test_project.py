"""
test_project.py
Test suite for Credit Card Eligibility Prediction project.
Run: python test_project.py
"""
import warnings
warnings.filterwarnings("ignore")
import sys, os, ast
from pathlib import Path

PASS = "PASS"
FAIL = "FAIL"
BASE = Path(__file__).resolve().parent

results = []

def check(label, ok, detail=""):
    tag = PASS if ok else FAIL
    msg = f"  [{tag}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append(ok)

print("=" * 60)
print("CREDIT ELIGIBILITY PROJECT — TEST SUITE")
print("=" * 60)

# ── Test 1: Model load ──────────────────────────────────────────
print("\nTEST 1: Model load & prediction")
try:
    import joblib
    pkg = joblib.load(os.path.join(BASE, "model", "model_package.joblib"))
    threshold     = pkg["threshold"]
    feature_names = pkg["feature_names"]
    model         = pkg["model"]
    check("Model keys present (model, threshold, feature_names)", True,
          f"threshold={threshold}, features={len(feature_names)}")
    check("Threshold value == 0.16", threshold == 0.16, str(threshold))
    check("Feature count == 23", len(feature_names) == 23, str(len(feature_names)))
except Exception as e:
    check("Model load", False, str(e))

# ── Test 2: Predictions ─────────────────────────────────────────
print("\nTEST 2: Prediction output")
try:
    import pandas as pd
    rows = [
        # Actual rows from CSV dataset (23 features each)
        [150000,2,2,1,49,1,-1,-1,-1,-1,-1,0,1870,669,0,13453,5773,1870,669,0,13453,5773,100],
        [80000,2,2,1,42,0,0,-1,-1,0,0,43024,9821,600,53900,55000,65000,5098,600,53900,1100,10000,0],
        [200000,2,2,1,31,-1,-1,-1,-1,-1,-1,1319,4997,3635,130,1209,938,4997,3650,130,1209,938,105],
    ]
    for i, row in enumerate(rows, 1):
        df   = pd.DataFrame([row], columns=feature_names)
        prob = model.predict_proba(df)[0]
        dp   = prob[1]
        ndp  = prob[0]
        ok1  = 0 <= dp <= 1 and 0 <= ndp <= 1
        ok2  = abs(dp + ndp - 1.0) < 1e-6
        score = max(0, min(100, round(100*(1-dp))))
        status = "APPROVED" if dp < threshold else "NOT APPROVED"
        check(f"Row {i} probabilities valid", ok1, f"P(def)={dp:.4f}")
        check(f"Row {i} probabilities sum to 1", ok2)
        check(f"Row {i} score in [0,100]", 0 <= score <= 100, str(score))
        check(f"Row {i} status is APPROVED or NOT APPROVED",
              status in ("APPROVED", "NOT APPROVED"), status)
except Exception as e:
    check("Prediction test", False, str(e))

# ── Test 3: Score formula ───────────────────────────────────────
print("\nTEST 3: Estimated Credit Health Score formula")
cases = [(0.10, 90), (0.20, 80), (0.50, 50), (0.00, 100), (1.00, 0)]
for dp, expected in cases:
    got = max(0, min(100, round(100*(1-dp))))
    check(f"P(def)={dp} -> Score={expected}", got == expected, f"got {got}")

# ── Test 4: Threshold logic ─────────────────────────────────────
print("\nTEST 4: Decision threshold logic")
cases = [(0.05, True, "APPROVED"), (0.16, False, "NOT APPROVED"), (0.80, False, "NOT APPROVED")]
for dp, exp_approved, exp_status in cases:
    approved = dp < threshold
    status   = "APPROVED" if approved else "NOT APPROVED"
    check(f"P(def)={dp} -> {exp_status}",
          approved == exp_approved and status == exp_status)

# ── Test 5: CSV dataset ─────────────────────────────────────────
print("\nTEST 5: CSV dataset structure")
try:
    df = pd.read_csv(os.path.join(BASE, "database", "credit_card_default_under_1mb.csv"))
    check("Shape is (9000, 25)", df.shape == (9000, 25), str(df.shape))
    check("'ID' column exists", "ID" in df.columns)
    check("Target column exists", "default payment next month" in df.columns)
    expected_features = [
        "LIMIT_BAL","SEX","EDUCATION","MARRIAGE","AGE",
        "PAY_0","PAY_2","PAY_3","PAY_4","PAY_5","PAY_6",
        "BILL_AMT1","BILL_AMT2","BILL_AMT3","BILL_AMT4","BILL_AMT5","BILL_AMT6",
        "PAY_AMT1","PAY_AMT2","PAY_AMT3","PAY_AMT4","PAY_AMT5","PAY_AMT6",
    ]
    all_present = all(c in df.columns for c in expected_features)
    check("All 23 model features present in CSV", all_present)
    check("No missing values in feature columns",
          df[expected_features].isnull().sum().sum() == 0)
except Exception as e:
    check("CSV load", False, str(e))

# ── Test 6: Python syntax ───────────────────────────────────────
print("\nTEST 6: Python file syntax")
py_files = ["backend/main.py", "backend/import_data.py"]
for rel in py_files:
    path = os.path.join(BASE, rel.replace("/", os.sep))
    try:
        with open(path, encoding="utf-8") as f:
            ast.parse(f.read())
        check(f"{rel} parses cleanly", True)
    except SyntaxError as e:
        check(f"{rel} parses cleanly", False, str(e))
    except FileNotFoundError:
        check(f"{rel} parses cleanly", False, "File not found")

# ── Test 7: Required files ──────────────────────────────────────
print("\nTEST 7: Required project files exist")
required = [
    "backend/main.py",
    "backend/import_data.py",
    "frontend/index.html",
    "frontend/style.css",
    "frontend/app.js",
    "model/model_package.joblib",
    "database/database.sql",
    "database/credit_card_default_under_1mb.csv",
    "requirements.txt",
    ".env.example",
    ".gitignore",
    "render.yaml",
    "README.md",
    "GITHUB_GUIDE.md",
    "RENDER_GUIDE.md",
    "DEPLOYMENT_GUIDE.md",
]
for rel in required:
    path = os.path.join(BASE, rel.replace("/", os.sep))
    check(rel, os.path.exists(path))

# ── Test 8: Content checks ──────────────────────────────────────
print("\nTEST 8: Key content checks")
# .env.example should not contain real passwords
with open(os.path.join(BASE, ".env.example")) as f:
    env_content = f.read()
check(".env.example has DB_HOST", "DB_HOST" in env_content)
check(".env.example has DB_PASSWORD placeholder", "DB_PASSWORD" in env_content)
check(".env.example does NOT hardcode real password",
      "your_mysql_password_here" in env_content)

# .gitignore excludes .env
with open(os.path.join(BASE, ".gitignore")) as f:
    gi = f.read()
check(".gitignore excludes .env", ".env" in gi)

# render.yaml has correct start command
with open(os.path.join(BASE, "render.yaml")) as f:
    ry = f.read()
check("render.yaml has uvicorn start command", "uvicorn backend.main:app" in ry)

# requirements.txt has key packages
with open(os.path.join(BASE, "requirements.txt")) as f:
    req = f.read()
for pkg in ["fastapi", "uvicorn", "sqlalchemy", "mysql-connector-python",
            "scikit-learn", "joblib", "pandas"]:
    check(f"requirements.txt contains {pkg}", pkg in req)

# ── Summary ─────────────────────────────────────────────────────
total  = len(results)
passed = sum(results)
failed = total - passed
print()
print("=" * 60)
print(f"RESULTS: {passed}/{total} tests passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASSED ✅")
else:
    print("SOME TESTS FAILED ❌ — review output above")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
