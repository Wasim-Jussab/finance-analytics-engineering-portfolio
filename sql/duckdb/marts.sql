CREATE SCHEMA IF NOT EXISTS mart;

CREATE OR REPLACE TABLE mart.dim_customer AS
SELECT
    customer_id,
    concat_ws(' ', first_name, last_name) AS full_name,
    date_of_birth,
    postcode
FROM raw.customers;

CREATE OR REPLACE TABLE mart.fct_payment AS
SELECT
    payment_id,
    account_id,
    payment_date,
    strftime(payment_date, '%Y-%m') AS payment_month,
    amount,
    payment_status,
    payment_method,
    payment_status = 'Completed' AS is_successful
FROM raw.payments;

CREATE OR REPLACE TABLE mart.dim_loan AS
WITH payment_summary AS (
    SELECT
        account_id,
        COUNT(*) FILTER (WHERE payment_status = 'Completed') AS completed_payment_count,
        COALESCE(SUM(amount) FILTER (WHERE payment_status = 'Completed'), 0.00)
            AS completed_payment_amount,
        MAX(payment_date) FILTER (WHERE payment_status = 'Completed')
            AS last_completed_payment_date
    FROM raw.payments
    GROUP BY account_id
),
run_parameters AS (
    SELECT as_of_date FROM raw.run_parameters
)
SELECT
    loan.account_id,
    loan.customer_id,
    loan.product_code,
    loan.origination_date,
    date_diff('month', loan.origination_date, run_parameters.as_of_date)
        - CASE
            WHEN day(run_parameters.as_of_date) < day(loan.origination_date) THEN 1
            ELSE 0
          END AS loan_age_months,
    loan.original_balance,
    loan.status,
    COALESCE(payment_summary.completed_payment_count, 0) AS completed_payment_count,
    COALESCE(payment_summary.completed_payment_amount, 0.00) AS completed_payment_amount,
    payment_summary.last_completed_payment_date
FROM raw.loans AS loan
CROSS JOIN run_parameters
LEFT JOIN payment_summary USING (account_id);
