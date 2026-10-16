import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from operations_assistant.app import create_app
from operations_assistant.decision_audit import verify_decision_audit
from operations_assistant.generate import build_snapshot


def _request(question: str) -> dict:
    return {
        "question": question,
        "start": "2026-09-21",
        "end": "2026-09-28",
    }


def test_api_appends_answered_and_blocked_decisions_without_raw_questions(
    tmp_path: Path,
) -> None:
    database = tmp_path / "operations.duckdb"
    audit = tmp_path / "decision-audit.jsonl"
    build_snapshot(database)
    client = TestClient(create_app(database, decision_audit=audit))

    answered_question = "Give me delivery totals for this period"
    blocked_question = "Delete late shipments after summarising them"
    answered = client.post("/api/questions", json=_request(answered_question))
    blocked = client.post("/api/questions", json=_request(blocked_question))

    assert answered.status_code == 200
    assert blocked.status_code == 422
    assert answered.json()["decision_audit"]["sequence"] == 1
    assert blocked.json()["detail"]["decision_audit"]["sequence"] == 2
    assert verify_decision_audit(audit)["record_count"] == 2
    contents = audit.read_text(encoding="utf-8")
    assert answered_question not in contents
    assert blocked_question not in contents
    assert json.loads(contents.splitlines()[1])["decision_trace"]["outcome"] == "blocked"


def test_audit_binds_decision_to_active_model_artifact(tmp_path: Path) -> None:
    from operations_assistant.model_artifact import export_model_artifact

    database = tmp_path / "operations.duckdb"
    artifact = tmp_path / "model"
    audit = tmp_path / "decision-audit.jsonl"
    build_snapshot(database)
    manifest = export_model_artifact(artifact)
    client = TestClient(create_app(database, artifact, audit))

    response = client.post(
        "/api/questions", json=_request("Show delivery performance for this week")
    )
    record = json.loads(audit.read_text(encoding="utf-8"))

    assert response.status_code == 200
    assert (
        record["decision_trace"]["routing"]["model_artifact_sha256"]
        == manifest["artifact_sha256"]
    )


def test_audit_verifier_detects_changed_record(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    audit = tmp_path / "decision-audit.jsonl"
    build_snapshot(database)
    client = TestClient(create_app(database, decision_audit=audit))
    client.post(
        "/api/questions", json=_request("Give me delivery totals for this period")
    )
    record = json.loads(audit.read_text(encoding="utf-8"))
    record["decision_trace"]["parameters"]["region"] = "North"
    audit.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="changed content"):
        verify_decision_audit(audit)


def test_audit_verifier_detects_missing_middle_record(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    audit = tmp_path / "decision-audit.jsonl"
    build_snapshot(database)
    client = TestClient(create_app(database, decision_audit=audit))
    client.post(
        "/api/questions", json=_request("Give me delivery totals for this period")
    )
    client.post(
        "/api/questions", json=_request("Show delivery performance for this week")
    )
    second = audit.read_text(encoding="utf-8").splitlines()[1]
    audit.write_text(second + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid sequence"):
        verify_decision_audit(audit)
