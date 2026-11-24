from pathlib import Path

import duckdb


def test_minimum_rank_covers_threshold_without_inventing_absent_directions():
    ranked = Path("models/marts/rpt_loan_shortfall_change_ranked.sql").read_text()
    ranked = ranked.replace("{{ ref('rpt_loan_monthly_shortfall_contribution') }}", "fixture")
    aggregate = Path("models/marts/agg_loan_shortfall_concentration.sql").read_text()
    aggregate = aggregate.replace("{{ ref('rpt_loan_shortfall_change_ranked') }}", "ranked")
    with duckdb.connect() as con:
        con.execute("""
            create table fixture as select date '2025-02-28' snapshot_date,
                id account_id, known has_previous_month,
                delta scheduled_principal_shortfall_change
            from (values ('A',true,80),('B',true,20),('C',true,-9),
                ('D',true,-3),('E',true,0),('F',false,null)) t(id,known,delta);
            insert into fixture values (date '2025-03-31','G',true,20);
            insert into fixture values (date '2025-04-30','H',false,null);
        """)
        con.execute("create view ranked as " + ranked)
        rows = con.execute(
            "select snapshot_date::varchar, change_direction, contributing_account_count, "
            "accounts_to_review_threshold, covered_gross_change_amount, "
            "covered_gross_change_share, previous_rank_gross_change_share from (" + aggregate + ") "
            "order by snapshot_date, change_direction"
        ).fetchall()
    assert rows == [
        ("2025-02-28", "Decrease", 2, 2, 12, 1, 0.75),
        ("2025-02-28", "Increase", 2, 1, 80, 0.8, None),
        ("2025-03-31", "Increase", 1, 1, 20, 1, None),
    ]


def test_tied_accounts_cross_exactly_at_eighty_percent_in_id_order():
    ranked = Path("models/marts/rpt_loan_shortfall_change_ranked.sql").read_text()
    ranked = ranked.replace("{{ ref('rpt_loan_monthly_shortfall_contribution') }}", "fixture")
    aggregate = Path("models/marts/agg_loan_shortfall_concentration.sql").read_text()
    aggregate = aggregate.replace("{{ ref('rpt_loan_shortfall_change_ranked') }}", "ranked")
    with duckdb.connect() as con:
        con.execute("""
            create table fixture as select date '2025-05-31' snapshot_date,
                id account_id, true has_previous_month,
                delta scheduled_principal_shortfall_change
            from (values ('B',40),('A',40),('C',20)) t(id,delta);
        """)
        con.execute("create view ranked as " + ranked)
        assert con.execute("select account_id from ranked order by direction_rank").fetchall() == [
            ("A",),
            ("B",),
            ("C",),
        ]
        assert con.execute(
            "select accounts_to_review_threshold, covered_gross_change_amount, "
            "covered_gross_change_share, previous_rank_gross_change_share from (" + aggregate + ")"
        ).fetchone() == (2, 80, 0.8, 0.4)
