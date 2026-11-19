from pathlib import Path

import duckdb


def test_contributions_cover_entries_exits_continuing_accounts_and_gaps():
    sql = Path("models/marts/rpt_loan_monthly_shortfall_contribution.sql").read_text()
    sql = sql.replace("{{ ref('fct_loan_monthly_schedule_position') }}", "fixture")
    with duckdb.connect() as connection:
        connection.execute("""
            create table fixture (
                snapshot_date date, account_id varchar, product_code varchar,
                scheduled_principal_shortfall_amount decimal(12,2)
            );
            insert into fixture values
                ('2025-01-31','A','P',10), ('2025-01-31','B','P',20),
                ('2025-02-28','A','P',15), ('2025-02-28','C','Q',30),
                ('2025-04-30','A','P',99);
        """)
        connection.execute("create view report as " + sql)
        rows = connection.execute("""
            select account_id, position_state, scheduled_principal_shortfall_amount,
                previous_scheduled_principal_shortfall_amount, scheduled_principal_shortfall_change
            from report where snapshot_date = date '2025-02-28' order by account_id
        """).fetchall()
        assert rows == [
            ("A", "Continuing", 15, 10, 5),
            ("B", "Exited", 0, 20, -20),
            ("C", "Entered", 30, 0, 30),
        ]
        assert connection.execute("""
            select sum(scheduled_principal_shortfall_change)
            from report where snapshot_date = date '2025-02-28'
        """).fetchone() == (15,)
        assert connection.execute("""
            select count(*) from report
            where snapshot_date in (date '2025-01-31', date '2025-04-30')
                and (position_state <> 'No comparator' or has_previous_month
                    or previous_scheduled_principal_shortfall_amount is not null
                    or scheduled_principal_shortfall_change is not null)
        """).fetchone() == (0,)
