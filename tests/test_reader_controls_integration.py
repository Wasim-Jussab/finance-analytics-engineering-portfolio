import json

import duckdb
import pytest

from finance_portfolio.lock_status import inspect_lock
from finance_portfolio.reader_lifecycle import diagnose, observe
from finance_portfolio.reader_readiness import probe_database
from finance_portfolio.run_pipeline import PipelineLockedError


@pytest.mark.parametrize("assignment_id,expected", [(1, "ready"), (2, "inconsistent")])
def test_readable_raw_data_does_not_prove_case_membership(tmp_path, assignment_id, expected):
    db = tmp_path / "finance.duckdb"
    with duckdb.connect(str(db)) as connection:
        connection.execute(
            """
            create schema raw; create schema mart;
            create table raw.loans as select 1 account_id;
            create table mart.rpt_loan_case_activity_summary as
                select 1 account_id, date '2025-12-31' as_of_date;
            create table mart.rpt_loan_current_assignment_action as
                select ? account_id, date '2025-12-31' as_of_date;
        """,
            [assignment_id],
        )
        connection.execute("""
            create table mart.agg_loan_case_team_coverage as select 1 account_count;
            create table mart.agg_loan_assignment_action_coverage as
                select 1 queue_account_count;
        """)
    before = db.read_bytes()
    assert observe(db)["readable"] is True
    assert probe_database(db)["status"] == expected
    assert db.read_bytes() == before


def test_completed_run_evidence_does_not_bypass_pipeline_lock(tmp_path):
    run = "12345678-1234-1234-1234-123456789abc"
    lock = tmp_path / "pipeline.lock"
    lock.write_text(json.dumps({"run_id": run, "process_id": 42, "started_at": "start"}))
    (tmp_path / f"{run}.json").write_text(
        json.dumps(
            {
                "run_id": run,
                "started_at": "start",
                "finished_at": "finish",
                "status": "succeeded",
            }
        )
    )
    before = lock.read_bytes()
    assert inspect_lock(lock, tmp_path)["status"] == "retained_completed_run"

    def forbidden_runner(step, root):
        raise AssertionError("A held lock must prevent every pipeline stage")

    with pytest.raises(PipelineLockedError):
        diagnose(
            tmp_path / "absent.duckdb",
            tmp_path,
            tmp_path / "new.json",
            lock,
            runner=forbidden_runner,
        )
    assert lock.read_bytes() == before
    assert not (tmp_path / "new.json").exists()
