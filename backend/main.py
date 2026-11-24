
"""
Credit Card Eligibility Prediction - FastAPI Backend
=====================================================
Connects to MySQL, loads the trained ML model, generates
predictions, calculates Credit Health Score and stores history.
"""

import os
import warnings
import logging
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pydantic import BaseModel, Field

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv

warnings.filterwarnings("ignore")

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, "..", ".env"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "credit_risk_db")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = URL.create(
    "mysql+mysqlconnector",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)

MODEL_PATH = os.getenv(
    "MODEL_PATH",
    os.path.join(
        BASE_DIR,
        "..",
        "model",
        "model_package.joblib"
    )
)

MODEL_PATH = os.path.abspath(MODEL_PATH)

# ============================================================
# FEATURE NAMES
# ============================================================

FEATURE_NAMES = [
    "LIMIT_BAL",
    "SEX",
    "EDUCATION",
    "MARRIAGE",
    "AGE",
    "PAY_0",
    "PAY_2",
    "PAY_3",
    "PAY_4",
    "PAY_5",
    "PAY_6",
    "BILL_AMT1",
    "BILL_AMT2",
    "BILL_AMT3",
    "BILL_AMT4",
    "BILL_AMT5",
    "BILL_AMT6",
    "PAY_AMT1",
    "PAY_AMT2",
    "PAY_AMT3",
    "PAY_AMT4",
    "PAY_AMT5",
    "PAY_AMT6"
]

# ============================================================
# GLOBAL VARIABLES
# ============================================================

engine = None
model_package = {}

# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_engine():

    global engine

    if engine is None:

        try:

            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=5,
                max_overflow=10
            )

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("MySQL connection established successfully.")

        except Exception as exc:

            logger.exception("MySQL connection failed")

            if engine is not None:
                engine.dispose()
                engine = None

            raise HTTPException(
                status_code=503,
                detail=f"Database connection failed: {exc}"
            )

    return engine


# ============================================================
# MODEL LOADING
# ============================================================

def load_model():

    global model_package

    try:

        logger.info("Loading model from: %s", MODEL_PATH)

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model file not found: {MODEL_PATH}"
            )

        package = joblib.load(MODEL_PATH)

        if not isinstance(package, dict):
            raise ValueError(
                "Model package must contain a dictionary."
            )

        if "model" not in package:
            raise ValueError("Model key missing in model package.")

        if "threshold" not in package:
            raise ValueError("Threshold missing in model package.")

        if "feature_names" not in package:
            raise ValueError("Feature names missing in model package.")

        if len(package["feature_names"]) != len(FEATURE_NAMES):
            raise ValueError(
                "Model feature count does not match backend features."
            )

        model_package = package

        logger.info(
            "Model loaded successfully. Threshold: %.2f",
            model_package["threshold"]
        )

    except Exception as exc:

        logger.exception("Model loading failed")

        raise RuntimeError(
            f"Unable to load ML model: {exc}"
        )


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    load_model()

    try:
        get_engine()
    except Exception:
        logger.exception(
            "Database is not currently available during startup."
        )

    yield

    global engine

    if engine is not None:
        engine.dispose()
        engine = None

    logger.info("Application shutdown completed.")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Credit Card Eligibility Prediction API",
    description=(
        "Bank Officer Dashboard API. "
        "Retrieves customer data from MySQL, "
        "runs the trained ML model and saves prediction history."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ============================================================
# VALUE MAPPINGS
# ============================================================

SEX_MAP = {
    1: "Male",
    2: "Female"
}

EDUCATION_MAP = {
    0: "Unknown",
    1: "Graduate School",
    2: "University",
    3: "High School",
    4: "Others",
    5: "Unknown",
    6: "Unknown"
}

MARRIAGE_MAP = {
    0: "Unknown",
    1: "Married",
    2: "Single",
    3: "Others"
}

# ============================================================
# CREDIT SCORE AND RISK CALCULATION
# ============================================================

def compute_prediction(features_df: pd.DataFrame) -> dict:

    model = model_package["model"]

    threshold = float(model_package["threshold"])

    probabilities = model.predict_proba(features_df)[0]

    classes = list(model.classes_)

    if 1 not in classes or 0 not in classes:
        raise ValueError(
            "The model must contain classes 0 and 1."
        )

    default_prob = float(probabilities[classes.index(1)])

    no_default_prob = float(probabilities[classes.index(0)])

    # Credit Health Score
    credit_score = round(100 * (1 - default_prob))

    credit_score = max(0, min(100, credit_score))

    # Eligibility
    is_approved = default_prob < threshold

    card_status = (
        "APPROVED"
        if is_approved
        else "NOT APPROVED"
    )

    # Score category
    if credit_score >= 80:
        category = "Excellent"

    elif credit_score >= 60:
        category = "Good"

    elif credit_score >= 40:
        category = "Fair"

    elif credit_score >= 20:
        category = "Poor"

    else:
        category = "Very Poor"

    # Risk level
    if default_prob < 0.20:
        risk_label = "Low Risk"

    elif default_prob < 0.40:
        risk_label = "Moderate Risk"

    elif default_prob < 0.60:
        risk_label = "High Risk"

    else:
        risk_label = "Very High Risk"

    return {
        "default_probability": round(default_prob, 4),

        "no_default_probability": round(no_default_prob, 4),

        "threshold": round(threshold, 4),

        "credit_health_score": credit_score,

        "score_category": category,

        "risk_label": risk_label,

        "credit_card_status": card_status,

        "is_approved": is_approved
    }


# ============================================================
# PYDANTIC MODELS
# ============================================================

class PredictionResult(BaseModel):

    user_id: int

    limit_bal: float

    sex: str
    education: str
    marriage: str

    age: int

    pay_0: int
    pay_2: int
    pay_3: int
    pay_4: int
    pay_5: int
    pay_6: int

    bill_amt1: float
    bill_amt2: float
    bill_amt3: float
    bill_amt4: float
    bill_amt5: float
    bill_amt6: float

    pay_amt1: float
    pay_amt2: float
    pay_amt3: float
    pay_amt4: float
    pay_amt5: float
    pay_amt6: float

    default_probability: float
    no_default_probability: float

    threshold: float

    credit_health_score: int

    score_category: str
    risk_label: str

    credit_card_status: str

    is_approved: bool

    prediction_id: Optional[int] = None

    prediction_date: Optional[str] = None


class HistoryItem(BaseModel):

    prediction_id: int
    user_id: int

    default_probability: float
    no_default_probability: float

    estimated_credit_score: int

    credit_card_status: str

    prediction_date: str


class UserLookupRequest(BaseModel):

    user_id: int = Field(
        ...,
        description="Customer ID",
        example=20174
    )


# ============================================================
# CUSTOMER PREDICTION FUNCTION
# ============================================================

def generate_prediction(user_id: int):

    if not model_package:
        raise HTTPException(
            status_code=503,
            detail="ML model is not loaded."
        )

    eng = get_engine()

    # --------------------------------------------------------
    # 1. FETCH CUSTOMER
    # --------------------------------------------------------

    try:

        with eng.connect() as conn:

            row = conn.execute(
                text("""
                    SELECT *
                    FROM customers
                    WHERE user_id = :uid
                """),
                {"uid": user_id}
            ).mappings().fetchone()

    except SQLAlchemyError as exc:

        logger.exception("Customer database query failed")

        raise HTTPException(
            status_code=503,
            detail=f"Customer database error: {exc}"
        )

    if row is None:

        raise HTTPException(
            status_code=404,
            detail=f"Customer ID {user_id} not found."
        )

    row = dict(row)

    # --------------------------------------------------------
    # 2. BUILD FEATURE DATAFRAME
    # --------------------------------------------------------

    try:

        features = {}

        for feature in FEATURE_NAMES:

            column_name = feature.lower()

            if column_name not in row:
                raise ValueError(
                    f"Missing customer column: {column_name}"
                )

            features[feature] = row[column_name]

        features_df = pd.DataFrame(
            [features],
            columns=FEATURE_NAMES
        )

    except Exception as exc:

        logger.exception("Feature preparation failed")

        raise HTTPException(
            status_code=500,
            detail=f"Feature preparation error: {exc}"
        )

    # --------------------------------------------------------
    # 3. ML PREDICTION
    # --------------------------------------------------------

    try:

        pred = compute_prediction(features_df)

        logger.info(
            "Prediction generated for customer %s",
            user_id
        )

    except Exception as exc:

        logger.exception("ML prediction failed")

        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {exc}"
        )

    # --------------------------------------------------------
    # 4. SAVE PREDICTION HISTORY
    # --------------------------------------------------------

    pred_id = None

    pred_date_db = datetime.now(timezone.utc).replace(
        tzinfo=None
    )

    pred_date = pred_date_db.isoformat()

    try:

        with eng.begin() as conn:

            result = conn.execute(
                text("""
                    INSERT INTO prediction_history
                    (
                        user_id,
                        default_probability,
                        no_default_probability,
                        estimated_credit_score,
                        credit_card_status,
                        prediction_date
                    )
                    VALUES
                    (
                        :uid,
                        :dp,
                        :ndp,
                        :score,
                        :status,
                        :dt
                    )
                """),
                {
                    "uid": user_id,

                    "dp": pred["default_probability"],

                    "ndp": pred["no_default_probability"],

                    "score": pred["credit_health_score"],

                    "status": pred["credit_card_status"],

                    "dt": pred_date_db
                }
            )

            pred_id = result.lastrowid

        logger.info(
            "Prediction history saved successfully. ID: %s",
            pred_id
        )

    except SQLAlchemyError as exc:

        logger.exception("Prediction history insertion failed")

        raise HTTPException(
            status_code=500,
            detail=f"Prediction history saving failed: {exc}"
        )

    # --------------------------------------------------------
    # 5. RETURN COMPLETE RESULT
    # --------------------------------------------------------

    return PredictionResult(

        user_id=user_id,

        limit_bal=float(row["limit_bal"]),

        sex=SEX_MAP.get(
            int(row["sex"]),
            "Unknown"
        ),

        education=EDUCATION_MAP.get(
            int(row["education"]),
            "Unknown"
        ),

        marriage=MARRIAGE_MAP.get(
            int(row["marriage"]),
            "Unknown"
        ),

        age=int(row["age"]),

        pay_0=int(row["pay_0"]),
        pay_2=int(row["pay_2"]),
        pay_3=int(row["pay_3"]),
        pay_4=int(row["pay_4"]),
        pay_5=int(row["pay_5"]),
        pay_6=int(row["pay_6"]),

        bill_amt1=float(row["bill_amt1"]),
        bill_amt2=float(row["bill_amt2"]),
        bill_amt3=float(row["bill_amt3"]),
        bill_amt4=float(row["bill_amt4"]),
        bill_amt5=float(row["bill_amt5"]),
        bill_amt6=float(row["bill_amt6"]),

        pay_amt1=float(row["pay_amt1"]),
        pay_amt2=float(row["pay_amt2"]),
        pay_amt3=float(row["pay_amt3"]),
        pay_amt4=float(row["pay_amt4"]),
        pay_amt5=float(row["pay_amt5"]),
        pay_amt6=float(row["pay_amt6"]),

        prediction_id=pred_id,

        prediction_date=pred_date,

        **pred
    )


# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/", include_in_schema=False)
def root():

    frontend = os.path.abspath(
        os.path.join(BASE_DIR, "..", "frontend")
    )

    index_file = os.path.join(
        frontend,
        "index.html"
    )

    if os.path.exists(index_file):
        return FileResponse(index_file)

    return {
        "message": "Credit Card Eligibility Prediction API is running.",
        "docs": "/api/docs"
    }


# ------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health_check():

    model_ok = bool(model_package)

    db_ok = False

    try:

        eng = get_engine()

        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))

        db_ok = True

    except Exception:
        db_ok = False

    return {
        "status": "ok" if model_ok and db_ok else "degraded",

        "model_loaded": model_ok,

        "db_connected": db_ok,

        "database": DB_NAME,

        "timestamp": datetime.now(
            timezone.utc
        ).isoformat()
    }


# ------------------------------------------------------------
# PREDICTION API
# ------------------------------------------------------------

@app.get(
    "/api/predict/{user_id}",
    response_model=PredictionResult,
    tags=["Prediction"]
)
def predict_by_user_id(user_id: int):

    return generate_prediction(user_id)


@app.post(
    "/api/predict",
    response_model=PredictionResult,
    tags=["Prediction"]
)
def predict_by_body(payload: UserLookupRequest):

    return generate_prediction(payload.user_id)


# ------------------------------------------------------------
# CUSTOMER DETAILS API
# ------------------------------------------------------------

@app.get(
    "/api/customer/{user_id}",
    response_model=PredictionResult,
    tags=["Customers"]
)
def get_customer(user_id: int):

    return generate_prediction(user_id)


# ------------------------------------------------------------
# PREDICTION HISTORY API
# ------------------------------------------------------------

@app.get(
    "/api/history/{user_id}",
    response_model=list[HistoryItem],
    tags=["History"]
)
def get_prediction_history(
    user_id: int,
    limit: int = Query(default=10, ge=1, le=100)
):

    eng = get_engine()

    try:

        with eng.connect() as conn:

            rows = conn.execute(
                text("""
                    SELECT
                        prediction_id,
                        user_id,
                        default_probability,
                        no_default_probability,
                        estimated_credit_score,
                        credit_card_status,
                        prediction_date

                    FROM prediction_history

                    WHERE user_id = :uid

                    ORDER BY prediction_id DESC

                    LIMIT :lim
                """),
                {
                    "uid": user_id,
                    "lim": limit
                }
            ).mappings().fetchall()

    except SQLAlchemyError as exc:

        logger.exception("History retrieval failed")

        raise HTTPException(
            status_code=503,
            detail=f"History database error: {exc}"
        )

    return [
        HistoryItem(
            prediction_id=r["prediction_id"],

            user_id=r["user_id"],

            default_probability=float(
                r["default_probability"]
            ),

            no_default_probability=float(
                r["no_default_probability"]
            ),

            estimated_credit_score=int(
                r["estimated_credit_score"]
            ),

            credit_card_status=r["credit_card_status"],

            prediction_date=str(
                r["prediction_date"]
            )
        )

        for r in rows
    ]


# ------------------------------------------------------------
# DASHBOARD STATISTICS API
# ------------------------------------------------------------

@app.get("/api/stats", tags=["Stats"])
def dashboard_stats():

    eng = get_engine()

    try:

        with eng.connect() as conn:

            total_customers = conn.execute(
                text("""
                    SELECT COUNT(*)
                    FROM customers
                """)
            ).scalar() or 0

            total_predictions = conn.execute(
                text("""
                    SELECT COUNT(*)
                    FROM prediction_history
                """)
            ).scalar() or 0

            approved = conn.execute(
                text("""
                    SELECT COUNT(*)
                    FROM prediction_history
                    WHERE credit_card_status = 'APPROVED'
                """)
            ).scalar() or 0

            rejected = conn.execute(
                text("""
                    SELECT COUNT(*)
                    FROM prediction_history
                    WHERE credit_card_status = 'NOT APPROVED'
                """)
            ).scalar() or 0

    except SQLAlchemyError as exc:

        logger.exception("Dashboard statistics failed")

        raise HTTPException(
            status_code=503,
            detail=f"Statistics database error: {exc}"
        )

    return {
        "total_customers": total_customers,

        "total_predictions": total_predictions,

        "approved": approved,

        "rejected": rejected
    }


# ------------------------------------------------------------
# SAMPLE CUSTOMER IDS
# ------------------------------------------------------------

@app.get("/api/sample-ids", tags=["Customers"])
def get_sample_ids():

    return {
        "approved_samples": [
            1341, 7889, 23127, 28429, 4444
        ],

        "rejected_samples": [
            20174, 12767, 17501, 18209, 13406
        ]
    }


# ============================================================
# STATIC FRONTEND
# ============================================================

FRONTEND_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend")
)

if os.path.isdir(FRONTEND_DIR):

    app.mount(
        "/static",
        StaticFiles(directory=FRONTEND_DIR),
        name="static"
    )


# ============================================================
# END
# ============================================================
