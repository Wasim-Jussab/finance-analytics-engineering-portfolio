from pathlib import Path

import duckdb


def test_monthly_change_uses_calendar_predecessor_not_previous_observation():
    sql = Path("models/marts/rpt_loan_portfolio_monthly_change.sql").read_text()
    reference = "{{ ref('agg_loan_portfolio_total_monthly') }}"
    assert sql.count(reference) == 2
    with duckdb.connect() as connection:
        connection.execute("""
            create table positions (
                snapshot_date date,
                loan_account_count integer,
                scheduled_principal_due_amount decimal(12,2),
                assumed_allocated_completed_payment_amount decimal(12,2),
                scheduled_principal_shortfall_amount decimal(12,2)
            );
            insert into positions values
                ('2025-01-31', 2, 100, 40, 60),
                ('2025-02-28', 3, 180, 50, 130),
                ('2025-04-30', 3, 200, 70, 130);
        """)
        connection.execute("create view report as " + sql.replace(reference, "positions"))
        rows = connection.execute("""
            select has_previous_month, loan_account_count_change,
                scheduled_principal_due_change,
                assumed_allocated_completed_payment_change,
                scheduled_principal_shortfall_change
            from report order by snapshot_date
        """).fetchall()
    assert rows == [
        (False, None, None, None, None),
        (True, 1, 80, 10, 70),
        (False, None, None, None, None),
    ]
