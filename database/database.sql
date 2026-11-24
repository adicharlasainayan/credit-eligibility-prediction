-- ============================================================
--  database.sql  |  credit_risk_db
--  Credit Card Eligibility Prediction Project
-- ============================================================
--  Run this file against your MySQL server BEFORE importing data.
--  mysql -u root -p < database.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS credit_risk_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE credit_risk_db;

-- ─────────────────────────── Table: customers ───────────────────────────
-- Stores every customer record imported from the UCI dataset CSV.
-- user_id maps directly to the original "ID" column.

CREATE TABLE IF NOT EXISTS customers (
    user_id                     INT             NOT NULL,
    limit_bal                   DECIMAL(15, 2)  NOT NULL COMMENT 'Credit limit (NT dollar)',
    sex                         TINYINT         NOT NULL COMMENT '1=Male, 2=Female',
    education                   TINYINT         NOT NULL COMMENT '1=Graduate, 2=University, 3=High School, 4+=Other',
    marriage                    TINYINT         NOT NULL COMMENT '1=Married, 2=Single, 3=Others',
    age                         TINYINT         NOT NULL,
    pay_0                       TINYINT         NOT NULL COMMENT 'Repayment status Sep (most recent)',
    pay_2                       TINYINT         NOT NULL COMMENT 'Repayment status Aug',
    pay_3                       TINYINT         NOT NULL COMMENT 'Repayment status Jul',
    pay_4                       TINYINT         NOT NULL COMMENT 'Repayment status Jun',
    pay_5                       TINYINT         NOT NULL COMMENT 'Repayment status May',
    pay_6                       TINYINT         NOT NULL COMMENT 'Repayment status Apr',
    bill_amt1                   DECIMAL(15, 2)  NOT NULL COMMENT 'Bill statement Sep (NT dollar)',
    bill_amt2                   DECIMAL(15, 2)  NOT NULL COMMENT 'Bill statement Aug',
    bill_amt3                   DECIMAL(15, 2)  NOT NULL COMMENT 'Bill statement Jul',
    bill_amt4                   DECIMAL(15, 2)  NOT NULL COMMENT 'Bill statement Jun',
    bill_amt5                   DECIMAL(15, 2)  NOT NULL COMMENT 'Bill statement May',
    bill_amt6                   DECIMAL(15, 2)  NOT NULL COMMENT 'Bill statement Apr',
    pay_amt1                    DECIMAL(15, 2)  NOT NULL COMMENT 'Previous payment Sep (NT dollar)',
    pay_amt2                    DECIMAL(15, 2)  NOT NULL COMMENT 'Previous payment Aug',
    pay_amt3                    DECIMAL(15, 2)  NOT NULL COMMENT 'Previous payment Jul',
    pay_amt4                    DECIMAL(15, 2)  NOT NULL COMMENT 'Previous payment Jun',
    pay_amt5                    DECIMAL(15, 2)  NOT NULL COMMENT 'Previous payment May',
    pay_amt6                    DECIMAL(15, 2)  NOT NULL COMMENT 'Previous payment Apr',
    default_payment_next_month  TINYINT         NOT NULL COMMENT '1=Default, 0=No Default',

    PRIMARY KEY (user_id),
    INDEX idx_age          (age),
    INDEX idx_education    (education),
    INDEX idx_limit_bal    (limit_bal)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ─────────────────────────── Table: prediction_history ───────────────────────────
-- Stores every eligibility check performed by the Bank Officer.

CREATE TABLE IF NOT EXISTS prediction_history (
    prediction_id           INT             NOT NULL AUTO_INCREMENT,
    user_id                 INT             NOT NULL,
    default_probability     DECIMAL(8, 6)   NOT NULL COMMENT 'P(default) from Random Forest',
    no_default_probability  DECIMAL(8, 6)   NOT NULL COMMENT 'P(no default)',
    estimated_credit_score  TINYINT         NOT NULL COMMENT '= 100 × (1 - P(default))',
    credit_card_status      VARCHAR(20)     NOT NULL COMMENT 'APPROVED or NOT APPROVED',
    prediction_date         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY  (prediction_id),
    FOREIGN KEY  (user_id) REFERENCES customers(user_id) ON DELETE CASCADE,
    INDEX idx_ph_user    (user_id),
    INDEX idx_ph_date    (prediction_date),
    INDEX idx_ph_status  (credit_card_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ─────────────────────────── Sample validation query ───────────────────────────
-- After importing data run these to verify:
--   SELECT COUNT(*) FROM customers;          -- expect 9000
--   SELECT COUNT(*) FROM prediction_history; -- expect 0 (initially)
--   SELECT * FROM customers LIMIT 5;
