import subprocess
import sys
from pathlib import Path

import duckdb

from finance_portfolio.reader_lifecycle import diagnose, observe


def test_observer_reads_original_without_mutation(tmp_path):
    db = tmp_path / "source.duckdb"
    with duckdb.connect(str(db)) as connection:
        connection.execute("create schema raw; create table raw.loans as select 1 id")
    before = db.read_bytes()
    assert observe(db)["loan_count"] == 1
    assert db.read_bytes() == before


def test_missing_source_is_not_created(tmp_path):
    db = tmp_path / "missing.duckdb"
    assert observe(db)["readable"] is False
    assert not db.exists()


def test_wal_read_error_is_sanitised_and_evidence_is_retained(tmp_path, monkeypatch):
    db = tmp_path / "source.duckdb"
    wal = Path(f"{db}.wal")
    wal.write_text("diagnostic fixture")

    def failed_connect(path, **kwargs):
        assert kwargs == {"read_only": True}
        raise duckdb.CatalogException(f"Failure while replaying WAL file {wal}")

    monkeypatch.setattr(duckdb, "connect", failed_connect)
    result = observe(db)
    assert result["readable"] is False
    assert result["wal_present"] is True
    assert result["error_type"] == "CatalogException"
    assert str(wal) not in str(result)
    assert wal.read_text() == "diagnostic fixture"


def test_first_failed_read_is_retained_even_if_later_reads_recover(tmp_path):
    calls = []

    def runner(step, root):
        calls.append(step.name)
        return 0

    def observer(db):
        return {"readable": calls[-1] != "dbt_build", "loan_count": 25}

    result = diagnose(
        Path("unused"),
        tmp_path,
        tmp_path / "report.json",
        tmp_path / "pipeline.lock",
        runner=runner,
        observer=observer,
    )
    assert result["pipeline_status"] == "succeeded"
    assert result["first_unreadable_after_stage"] == "dbt_build"
    assert result["observations"][0]["after_stage"] == "load"
    assert not (tmp_path / "pipeline.lock").exists()


def test_failed_stage_stops_execution_but_still_gets_observed(tmp_path):
    result = diagnose(
        Path("unused"),
        tmp_path,
        tmp_path / "report.json",
        tmp_path / "pipeline.lock",
        runner=lambda step, root: 1 if step.name == "source_freshness" else 0,
        observer=lambda db: {"readable": False},
    )
    assert result["pipeline_status"] == "failed"
    assert [x["after_stage"] for x in result["observations"]] == ["load", "source_freshness"]


def test_cli_respects_existing_lock_without_writing_diagnostic(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    lock = reports / "pipeline.lock"
    lock.write_text('{"run_id":"existing-owner"}')
    result = subprocess.run(
        [sys.executable, "-m", "finance_portfolio.reader_lifecycle"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "No lock was removed" in result.stderr
    assert lock.read_text() == '{"run_id":"existing-owner"}'
    assert not (reports / "reader-lifecycle.json").exists()
