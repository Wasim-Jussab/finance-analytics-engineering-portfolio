from pathlib import Path

import duckdb
import pytest


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


def test_coverage_change_uses_unrounded_ratios_and_requires_both_denominators():
    sql = Path("models/marts/rpt_loan_portfolio_monthly_change.sql").read_text()
    reference = "{{ ref('agg_loan_portfolio_total_monthly') }}"
    with duckdb.connect() as connection:
        connection.execute("""
            create table positions (
                snapshot_date date, loan_account_count integer,
                scheduled_principal_due_amount decimal(12,2),
                assumed_allocated_completed_payment_amount decimal(12,2),
                scheduled_principal_shortfall_amount decimal(12,2)
            );
            insert into positions values
                ('2025-01-31', 2, 0, 0, 0),
                ('2025-02-28', 2, 100, 40, 60),
                ('2025-03-31', 2, 300, 100, 200),
                ('2025-04-30', 2, 300, 200, 100),
                ('2025-06-30', 2, 0, 0, 0);
        """)
        rows = connection.execute(
            "select due_principal_coverage_ratio, previous_due_principal_coverage_ratio, "
            "coverage_change_percentage_points from (" + sql.replace(reference, "positions")
            + ") order by snapshot_date"
        ).fetchall()
        effects = connection.execute(
            "select allocation_first_effect_percentage_points, due_second_effect_percentage_points "
            "from (" + sql.replace(reference, "positions") + ") order by snapshot_date"
        ).fetchall()
    assert rows[0] == (None, None, None)
    assert rows[1] == (0.4, None, None)
    assert rows[2] == pytest.approx((0.3333, 0.4, -6.666667))
    assert rows[3] == pytest.approx((0.6667, 0.3333, 33.333333))
    assert rows[4] == (None, None, None)
    assert effects[0] == effects[1] == effects[4] == (None, None)
    assert effects[2] == pytest.approx((60.0, -66.666667))
    assert effects[3] == pytest.approx((33.333333, 0.0))
    for row, effect in zip(rows, effects, strict=True):
        if row[2] is not None:
            assert sum(effect) == pytest.approx(row[2], abs=0.000002)
