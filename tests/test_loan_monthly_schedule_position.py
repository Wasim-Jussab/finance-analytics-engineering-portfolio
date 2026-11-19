from pathlib import Path

import duckdb


def test_account_month_allocation_caps_payments_and_excludes_future_due():
    sql = Path("models/marts/fct_loan_monthly_schedule_position.sql").read_text()
    sql = sql.replace("{{ ref('fct_loan_monthly_snapshot') }}", "snapshots")
    sql = sql.replace("{{ ref('fct_loan_repayment_schedule') }}", "schedule")
    with duckdb.connect() as connection:
        connection.execute("""
            create table snapshots (
                account_id varchar, product_code varchar, snapshot_date date,
                original_balance decimal(12,2), cumulative_completed_payment_amount decimal(12,2)
            );
            insert into snapshots values
                ('A', 'P', '2025-01-31', 100, 40),
                ('B', 'P', '2025-01-31', 100, 80),
                ('C', 'P', '2025-01-31', 100, 0);
            create table schedule (
                account_id varchar, due_date date, scheduled_principal_amount decimal(12,2)
            );
            insert into schedule values
                ('A', '2025-01-15', 50), ('A', '2025-02-15', 50),
                ('B', '2025-01-15', 50), ('B', '2025-02-15', 50),
                ('C', '2025-02-15', 50), ('C', '2025-03-15', 50);
        """)
        rows = connection.execute(
            "select account_id, scheduled_principal_due_amount, "
            "assumed_allocated_completed_payment_amount, scheduled_principal_shortfall_amount, "
            "future_scheduled_principal_amount, unallocated_completed_payment_amount "
            "from (" + sql + ") order by account_id"
        ).fetchall()
    assert rows == [("A", 50, 40, 10, 50, 0), ("B", 50, 50, 0, 50, 30), ("C", 0, 0, 0, 100, 0)]
