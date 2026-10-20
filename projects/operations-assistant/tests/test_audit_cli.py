import json
from pathlib import Path

from fastapi.testclient import TestClient
from operations_assistant.app import create_app
from operations_assistant.audit_cli import run
from operations_assistant.generate import build_snapshot


def _create_ledger(tmp_path: Path) -> tuple[Path, dict]:
    database = tmp_path / "operations.duckdb"
    audit = tmp_path / "decision-audit.jsonl"
    build_snapshot(database)
    client = TestClient(create_app(database, decision_audit=audit))
    response = client.post(
        "/api/questions",
        json={
            "question": "Give me delivery totals for this period",
            "start": "2026-09-21",
            "end": "2026-09-28",
        },
    )
    assert response.status_code == 200
    return audit, client.get("/api/audit/status").json()


def test_cli_verifies_ledger_and_external_expectations(
    tmp_path: Path, capsys
) -> None:
    audit, expected = _create_ledger(tmp_path)

    exit_code = run(
        [
            "--path",
            str(audit),
            "--expected-head-sha256",
            expected["head_record_sha256"],
            "--expected-record-count",
            str(expected["record_count"]),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["verification"] == "passed"
    assert output["external_expectation_checked"] is True
    assert output["record_count"] == 1
    assert str(audit) not in json.dumps(output)


def test_cli_returns_failure_without_exposing_ledger_content(
    tmp_path: Path, capsys
) -> None:
    audit, expected = _create_ledger(tmp_path)

    exit_code = run(
        [
            "--path",
            str(audit),
            "--expected-head-sha256",
            "0" * 64,
            "--expected-record-count",
            str(expected["record_count"]),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["verification"] == "failed"
    assert "external expectation" in output["reason"]
    assert str(audit) not in json.dumps(output)
    assert "decision_trace" not in output
