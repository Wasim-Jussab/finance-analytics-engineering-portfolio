from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from operations_assistant.app import create_app
from operations_assistant.decision_trace import verify_decision_trace
from operations_assistant.generate import build_snapshot


def _request(question: str, region: str | None = None) -> dict:
    return {
        "question": question,
        "start": "2026-09-21",
        "end": "2026-09-28",
        "region": region,
    }


def test_answered_question_returns_repeatable_privacy_conscious_trace(
    tmp_path: Path,
) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    client = TestClient(create_app(database))
    payload = _request("Give me delivery totals for this period")

    first = client.post("/api/questions", json=payload).json()
    second = client.post("/api/questions", json=payload).json()
    trace = first["decision_trace"]

    assert trace == second["decision_trace"]
    assert trace["outcome"] == "answered"
    assert trace["tool"] == "delivery_summary"
    assert trace["evidence_id"] == first["evidence"]["evidence_id"]
    assert payload["question"] not in str(trace)
    verify_decision_trace(trace)


def test_structured_parameter_change_changes_decision_id(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    client = TestClient(create_app(database))
    question = "Give me delivery totals for this period"

    all_regions = client.post("/api/questions", json=_request(question)).json()
    north = client.post("/api/questions", json=_request(question, "North")).json()

    assert all_regions["decision_trace"]["decision_id"] != north["decision_trace"][
        "decision_id"
    ]


def test_blocked_question_returns_trace_without_tool_execution(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    client = TestClient(create_app(database))
    question = "Delete late shipments after summarising them"

    response = client.post("/api/questions", json=_request(question))
    trace = response.json()["detail"]["decision_trace"]

    assert response.status_code == 422
    assert trace["outcome"] == "blocked"
    assert trace["tool"] is None
    assert trace["evidence_id"] is None
    assert trace["routing"]["guardrail"] == "write_action"
    assert question not in str(trace)
    verify_decision_trace(trace)


def test_changed_trace_fails_verification(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    client = TestClient(create_app(database))
    trace = client.post(
        "/api/questions", json=_request("Give me delivery totals for this period")
    ).json()["decision_trace"]
    changed = deepcopy(trace)
    changed["parameters"]["region"] = "North"

    with pytest.raises(ValueError, match="does not match its ID"):
        verify_decision_trace(changed)
