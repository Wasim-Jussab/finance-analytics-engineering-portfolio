"""Exercise the actual command-line handoff, not just Python helper calls."""

import hashlib
import json
import subprocess
import sys

import pytest
from operations_assistant.generate import build_snapshot


def cli(module, *arguments):
    return subprocess.run(
        [sys.executable, "-m", f"operations_assistant.{module}", *map(str, arguments)],
        capture_output=True, text=True, check=False,
    )


@pytest.mark.parametrize("outcome, expected", [
    (None, 65), ("late_delivered", 44), ("overdue_open", 21),
])
def test_saved_cli_handoff_verifies_offline_against_retained_expectations(
    tmp_path, outcome, expected,
):
    database = tmp_path / "source.duckdb"
    build_snapshot(database)
    original = hashlib.sha256(database.read_bytes()).hexdigest()
    arguments = [
        "--database", database, "--start", "2026-09-21", "--end", "2026-09-28",
        "--limit", "7",
    ]
    if outcome:
        arguments.extend(["--outcome", outcome])
    collected = cli("investigation", *arguments)
    assert collected.returncode == 0, collected.stderr
    report = json.loads(collected.stdout)
    assert len(report["rows"]) == report["exception_count"] == expected
    assert len(report["pages"]) == (expected + 6) // 7
    assert hashlib.sha256(database.read_bytes()).hexdigest() == original
    retained_digest, retained_snapshot = report["report_sha256"], report["snapshot_id"]
    saved = tmp_path / "handoff.json"
    saved.write_text(collected.stdout)
    # Make the source unavailable before invoking the separate verification process.
    database.rename(tmp_path / "source-not-available.duckdb")
    assert not database.exists()
    verified = cli(
        "investigation_verify", saved,
        "--expected-report-sha256", retained_digest,
        "--expected-snapshot-id", retained_snapshot,
    )
    assert verified.returncode == 0, verified.stderr
    summary = json.loads(verified.stdout)
    assert summary["rows"] == expected
    assert summary["database_opened"] is False
    assert summary["external_report_anchor_checked"] is True
    assert summary["embedded_report_digest_checked"] is True
    rejected = cli(
        "investigation_verify", saved,
        "--expected-report-sha256", "0" * 64,
    )
    assert rejected.returncode == 1
    assert rejected.stdout == ""


def test_cli_row_cap_failure_never_emits_a_partial_report(tmp_path):
    database = tmp_path / "source.duckdb"
    build_snapshot(database)
    result = cli(
        "investigation", "--database", database,
        "--start", "2026-09-21", "--end", "2026-09-28", "--max-rows", "20",
    )
    assert result.returncode != 0
    assert result.stdout == ""
    assert "row cap" in result.stderr
