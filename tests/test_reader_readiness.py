import hashlib
import json
import subprocess
import sys
from pathlib import Path

import duckdb

from finance_portfolio import reader_readiness


def healthy_database(path: Path):
    with duckdb.connect(str(path)) as connection:
        connection.execute("""
            create schema mart;
            create table mart.rpt_loan_case_activity_summary as select 1 as account_id;
            create table mart.rpt_loan_current_assignment_action as select 1 as account_id;
            create table mart.agg_loan_case_team_coverage as select 1 as account_count;
            create table mart.agg_loan_assignment_action_coverage as
                select 1 as queue_account_count;
        """)


def test_readable_database_is_reconciled_without_mutation(tmp_path: Path):
    path = tmp_path / "finance.duckdb"
    healthy_database(path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    report = reader_readiness.probe_database(path)
    assert report["status"] == "ready"
    assert report["reader_opened"] is True
    assert set(report["population_counts"].values()) == {1}
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_missing_database_is_not_created(tmp_path: Path):
    path = tmp_path / "missing.duckdb"
    assert reader_readiness.probe_database(path)["reason"] == "database_missing"
    assert not path.exists()


def test_filesystem_permission_error_is_sanitised(tmp_path: Path, monkeypatch):
    path = tmp_path / "private.duckdb"
    real_is_file = Path.is_file

    def fail_for_source(candidate):
        if candidate == path:
            raise PermissionError(str(path))
        return real_is_file(candidate)

    monkeypatch.setattr(Path, "is_file", fail_for_source)
    report = reader_readiness.probe_database(path)
    assert report["reason"] == "filesystem_access_error"
    assert report["status"] == "unavailable"
    assert str(path) not in json.dumps(report)


def test_population_mismatch_is_not_ready(tmp_path: Path):
    path = tmp_path / "finance.duckdb"
    healthy_database(path)
    with duckdb.connect(str(path)) as connection:
        connection.execute("update mart.agg_loan_case_team_coverage set account_count = 2")
    report = reader_readiness.probe_database(path)
    assert report["status"] == "inconsistent"
    assert report["reason"] == "case_population_mismatch"


def test_incomplete_schema_returns_no_partial_counts(tmp_path: Path):
    path = tmp_path / "finance.duckdb"
    with duckdb.connect(str(path)) as connection:
        connection.execute("create schema mart")
    report = reader_readiness.probe_database(path)
    assert report["status"] == "unavailable"
    assert report["reason"] == "database_read_error"
    assert report["population_counts"] is None
    assert str(path) not in json.dumps(report)


def test_wal_replay_failure_is_not_bypassed_or_deleted(tmp_path: Path, monkeypatch):
    path = tmp_path / "finance.duckdb"
    healthy_database(path)
    wal = Path(f"{path}.wal")
    wal.write_text("retained diagnostic fixture")
    before = path.read_bytes()

    def fail_read(database, **kwargs):
        assert kwargs == {"read_only": True}
        raise duckdb.CatalogException(f'Failure while replaying WAL file "{wal}": schema exists')

    monkeypatch.setattr(reader_readiness.duckdb, "connect", fail_read)
    report = reader_readiness.probe_database(path)
    assert report["status"] == "unavailable"
    assert report["reason"] == "wal_replay_error"
    assert report["population_counts"] is None
    assert path.read_bytes() == before
    assert wal.read_text() == "retained diagnostic fixture"
    assert str(path) not in json.dumps(report)


def test_readiness_cli_exit_codes(tmp_path: Path):
    path = tmp_path / "finance.duckdb"
    healthy_database(path)
    command = [sys.executable, "-m", "finance_portfolio.reader_readiness", "--database"]
    success = subprocess.run([*command, str(path)], capture_output=True, text=True, check=False)
    assert success.returncode == 0
    assert json.loads(success.stdout)["status"] == "ready"
    failed = subprocess.run(
        [*command, str(tmp_path / "missing")], capture_output=True, text=True, check=False
    )
    assert failed.returncode == 1
    assert json.loads(failed.stdout)["reason"] == "database_missing"
