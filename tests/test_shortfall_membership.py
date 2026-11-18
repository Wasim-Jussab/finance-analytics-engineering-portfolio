from pathlib import Path

import duckdb


def test_gross_changes_preserve_offsets_and_unknown_comparators():
    sql = Path("models/marts/agg_loan_shortfall_by_membership.sql").read_text()
    sql = sql.replace("{{ ref('rpt_loan_monthly_shortfall_contribution') }}", "fixture")
    with duckdb.connect() as connection:
        connection.execute("""
            create table fixture (
                snapshot_date date, previous_snapshot_date date, has_previous_month boolean,
                position_state varchar, scheduled_principal_shortfall_amount decimal(12,2),
                previous_scheduled_principal_shortfall_amount decimal(12,2),
                scheduled_principal_shortfall_change decimal(12,2)
            );
            insert into fixture values
                ('2025-01-31',null,false,'No comparator',50,null,null),
                ('2025-02-28','2025-01-31',true,'Continuing',15,10,5),
                ('2025-02-28','2025-01-31',true,'Continuing',5,8,-3),
                ('2025-02-28','2025-01-31',true,'Continuing',7,7,0),
                ('2025-02-28','2025-01-31',true,'Entered',30,0,30),
                ('2025-02-28','2025-01-31',true,'Exited',0,20,-20);
        """)
        rows = connection.execute(
            "select position_state, contribution_account_count, "
            "scheduled_principal_shortfall_change,"
            " gross_shortfall_increase_amount, gross_shortfall_decrease_amount, "
            "increasing_account_count, decreasing_account_count, unchanged_account_count "
            "from (" + sql + ") order by snapshot_date, position_state"
        ).fetchall()
    assert rows == [
        ("No comparator", 1, None, None, None, None, None, None),
        ("Continuing", 3, 2, 5, 3, 1, 1, 1),
        ("Entered", 1, 30, 30, 0, 1, 0, 0),
        ("Exited", 1, -20, 0, 20, 0, 1, 0),
    ]
