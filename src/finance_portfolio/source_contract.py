"""Executable column contract shared by data generation and ingestion."""

from __future__ import annotations

RAW_TABLES: dict[str, list[tuple[str, str]]] = {
    "subscription_plans": [
        ("subscription_plan_id", "VARCHAR"),
        ("product_code", "VARCHAR"),
        ("billing_frequency", "VARCHAR"),
        ("billing_amount", "DECIMAL(12, 2)"),
    ],
    "customers": [
        ("customer_id", "VARCHAR"),
        ("first_name", "VARCHAR"),
        ("last_name", "VARCHAR"),
        ("date_of_birth", "DATE"),
        ("postcode", "VARCHAR"),
    ],
    "loans": [
        ("account_id", "VARCHAR"),
        ("customer_id", "VARCHAR"),
        ("product_code", "VARCHAR"),
        ("origination_date", "DATE"),
        ("original_balance", "DECIMAL(12, 2)"),
        ("term_months", "INTEGER"),
        ("status", "VARCHAR"),
    ],
    "loan_repayment_schedule": [
        ("schedule_id", "VARCHAR"),
        ("account_id", "VARCHAR"),
        ("instalment_number", "INTEGER"),
        ("due_date", "DATE"),
        ("scheduled_principal_amount", "DECIMAL(12, 2)"),
    ],
    "subscriptions": [
        ("subscription_id", "VARCHAR"),
        ("customer_id", "VARCHAR"),
        ("product_code", "VARCHAR"),
        ("subscription_plan_id", "VARCHAR"),
        ("start_date", "DATE"),
        ("cancellation_date", "DATE"),
        ("billing_frequency", "VARCHAR"),
        ("status", "VARCHAR"),
    ],
    "subscription_payments": [
        ("subscription_payment_id", "VARCHAR"),
        ("subscription_id", "VARCHAR"),
        ("billing_date", "DATE"),
        ("amount", "DECIMAL(12, 2)"),
        ("payment_status", "VARCHAR"),
    ],
    "payments": [
        ("payment_id", "VARCHAR"),
        ("account_id", "VARCHAR"),
        ("payment_date", "DATE"),
        ("amount", "DECIMAL(12, 2)"),
        ("payment_status", "VARCHAR"),
        ("payment_method", "VARCHAR"),
    ],
}

TABLE_COLUMNS: dict[str, list[str]] = {
    table: [column_name for column_name, _ in columns]
    for table, columns in RAW_TABLES.items()
}
