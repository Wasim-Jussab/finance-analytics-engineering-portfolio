import hashlib
from datetime import date
from pathlib import Path

import duckdb
import pytest

from finance_portfolio.shortfall_review import build_review


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "synthetic.duckdb"
    ranked = Path("models/marts/rpt_loan_shortfall_change_ranked.sql").read_text()
    ranked = ranked.replace("{{ ref('rpt_loan_monthly_shortfall_contribution') }}", "fixture")
    summary = Path("models/marts/agg_loan_shortfall_concentration.sql").read_text()
    summary = summary.replace("{{ ref('rpt_loan_shortfall_change_ranked') }}", "mart.ranked")
    with duckdb.connect(str(path)) as con:
        con.execute("""
            create schema mart;
            create table fixture as select date '2025-02-28' snapshot_date,
                id account_id, true has_previous_month,
                delta::decimal(12,2) scheduled_principal_shortfall_change
            from (values ('A',80),('B',20),('C',-9),('D',-3),('E',0)) t(id,delta);
            insert into fixture values (date '2025-01-31','F',false,null);
            insert into fixture values (date '2025-03-31','G',true,0);
        """)
        con.execute("create view mart.ranked as " + ranked)
        con.execute(
            "create view mart.rpt_loan_shortfall_change_ranked as select * from mart.ranked"
        )
        con.execute("create view mart.agg_loan_shortfall_concentration as " + summary)
    return path


@pytest.mark.parametrize(
    ("direction", "amount", "share", "account"),
    [
        ("Increase", "80.00", 0.8, "A"),
        ("Decrease", "9.00", 0.75, "C"),
    ],
)
def test_bounded_review_keeps_full_denominator_and_database_unchanged(
    database, direction, amount, share, account
):
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    report = build_review(database, date(2025, 2, 28), direction, 1)
    assert report["returned_accounts"] == 1
    assert report["contributing_accounts"] == 2
    assert report["selected_gross_change_amount"] == amount
    assert report["selected_gross_change_share"] == share
    assert report["rows"][0]["account_id"] == account
    assert report["has_more"] is True
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before


def test_absent_direction_is_not_invented_as_zero(database):
    report = build_review(database, date(2025, 3, 31), "Decrease", 5)
    assert report["status"] == "direction_absent"
    assert report["direction_gross_change_amount"] is None
    assert report["selected_gross_change_share"] is None
    assert report["rows"] == []


@pytest.mark.parametrize("limit", [0, 51, True, 1.5])
def test_invalid_limit_is_refused(database, limit):
    with pytest.raises(ValueError, match="Limit"):
        build_review(database, date(2025, 2, 28), "Increase", limit)


@pytest.mark.parametrize(
    ("snapshot", "message"),
    [
        (date(2025, 1, 31), "Comparison month"),
        (date(2024, 12, 31), "Snapshot date"),
    ],
)
def test_unknown_month_or_comparator_is_refused(database, snapshot, message):
    with pytest.raises(ValueError, match=message):
        build_review(database, snapshot, "Increase")


def test_unapproved_direction_is_refused(database):
    with pytest.raises(ValueError, match="Direction"):
        build_review(database, date(2025, 2, 28), "arbitrary sql")


@pytest.mark.parametrize(
    "mutation",
    [
        "count",
        "gross",
        "missing",
        "duplicate_summary",
        "bad_ranks",
        "duplicate_accounts",
    ],
)
def test_inconsistent_models_are_refused_even_for_a_one_row_cap(database, mutation):
    with duckdb.connect(str(database)) as con:
        con.execute(
            "create table mart.summary_copy as select * from mart.agg_loan_shortfall_concentration"
        )
        con.execute(
            "create or replace view mart.agg_loan_shortfall_concentration "
            "as select * from mart.summary_copy"
        )
        if mutation == "count":
            con.execute("update mart.summary_copy set contributing_account_count=99")
        elif mutation == "gross":
            con.execute("update mart.summary_copy set direction_gross_change_amount=999")
        elif mutation == "missing":
            con.execute("delete from mart.summary_copy")
        elif mutation == "duplicate_summary":
            con.execute("insert into mart.summary_copy select * from mart.summary_copy")
        else:
            field = "3 as direction_rank" if mutation == "bad_ranks" else "'A' as account_id"
            con.execute(
                "create or replace view mart.rpt_loan_shortfall_change_ranked "
                "as select * replace (" + field + ") from mart.ranked"
            )
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="reconcile"):
        build_review(database, date(2025, 2, 28), "Increase", 1)
    assert hashlib.sha256(database.read_bytes()).hexdigest() == before
