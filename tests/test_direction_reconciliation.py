from pathlib import Path

import duckdb


def test_swapped_direction_counts_fail_even_when_partition_matches():
    sql = Path("tests/loan_shortfall_direction_reconciliation.sql").read_text()
    sql = sql.replace("{{ ref('agg_loan_shortfall_by_membership') }}", "summary")
    sql = sql.replace("{{ ref('rpt_loan_monthly_shortfall_contribution') }}", "accounts")
    with duckdb.connect() as con:
        con.execute("""
            create table accounts as select date '2025-02-28' snapshot_date,
                'Continuing' position_state, delta scheduled_principal_shortfall_change
            from (values (5),(-3),(0),(0)) t(delta);
            create table summary as select date '2025-02-28' snapshot_date,
                'Continuing' position_state, true has_previous_month,
                1 increasing_account_count, 1 decreasing_account_count, 2 unchanged_account_count;
        """)
        assert con.execute(sql).fetchall() == []
        con.execute("update summary set increasing_account_count=2, unchanged_account_count=1")
        # Still four accounts in total; each sign bucket must reconcile independently.
        assert len(con.execute(sql).fetchall()) == 1
