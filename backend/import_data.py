"""
import_data.py
=============
One-time script to import the CSV dataset into MySQL credit_risk_db.customers.
Run once after creating the database schema (database.sql).

Usage:
    python import_data.py
"""

import os
import sys
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "3306")
DB_NAME     = os.getenv("DB_NAME", "credit_risk_db")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

from sqlalchemy.engine import URL

DATABASE_URL = URL.create(
    "mysql+mysqlconnector",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)    

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "database", "credit_card_default_under_1mb.csv"
)


def import_csv():
    logger.info("Reading CSV from: %s", CSV_PATH)
    df = pd.read_csv(CSV_PATH)
    logger.info("Loaded %d rows × %d columns", *df.shape)

    # Rename columns to match the MySQL table (all lowercase)
    df.columns = [
        c.lower()
        .replace(" ", "_")
        .replace("default_payment_next_month", "default_payment_next_month")
        for c in df.columns
    ]

    # Ensure column names match table definition
    column_map = {
        "id":                           "user_id",
        "default_payment_next_month":   "default_payment_next_month",
    }
    df.rename(columns=column_map, inplace=True)

    logger.info("Columns after rename: %s", df.columns.tolist())

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("✅ Database connection OK.")

    # Import (replace existing rows on duplicate user_id)
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        conn.execute(text("TRUNCATE TABLE customers"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    df.to_sql(
        "customers",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=500,
        method="multi",
    )

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()

    logger.info("✅ Imported %d rows into customers table.", count)


if __name__ == "__main__":
    try:
        import_csv()
        print("\n✅ Dataset imported successfully into credit_risk_db.customers\n")
    except Exception as exc:
        logger.error("❌ Import failed: %s", exc)
        sys.exit(1)
