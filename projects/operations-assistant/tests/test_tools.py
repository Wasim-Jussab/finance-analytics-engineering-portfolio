import hashlib
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from operations_assistant.app import create_app
from operations_assistant.generate import build_snapshot, generate_rows
from operations_assistant.metrics import summary
from operations_assistant.tools import ToolRequest, execute_tool


def comparison():
    return {
        "name": "compare_delivery_periods",
        "start": "2026-09-21",
        "end": "2026-09-28",
        "baseline_start": "2026-09-14",
        "baseline_end": "2026-09-21",
    }


def test_tools_reconcile_to_service_without_changing_database(tmp_path: Path):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    fingerprint = hashlib.sha256(db.read_bytes()).hexdigest()
    result = execute_tool(db, ToolRequest.model_validate(comparison()))
    before = summary(db, date(2026, 9, 14), date(2026, 9, 21))
    after = summary(db, date(2026, 9, 21), date(2026, 9, 28))
    assert result["baseline"] == before
    assert result["current"] == after
    assert result["change"]["due_change"] == 5
    assert result["change"]["late_delivered_change"] == 17
    assert result["change"]["overdue_open_change"] == 11
    assert result["change"]["on_time_rate_change_percentage_points"] == pytest.approx(
        (153 / 218 - 176 / 213) * 100
    )
    for key in ("due_change", "on_time_change", "late_delivered_change", "overdue_open_change"):
        assert sum(r[key] for r in result["regional_changes"]) == result["change"][key]
    assert hashlib.sha256(db.read_bytes()).hexdigest() == fingerprint


def test_catalog_and_api_reject_unapproved_calls(tmp_path: Path):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    client = TestClient(create_app(db))
    assert client.get("/api/tools").json()["tools"] == [
        "delivery_summary",
        "compare_delivery_periods",
        "delivery_exceptions",
    ]
    response = client.post("/api/tools/execute", json=comparison())
    assert response.status_code == 200
    assert response.json()["mode"] == "deterministic"
    for invalid in (
        {**comparison(), "name": "execute_sql"},
        {**comparison(), "sql": "DELETE FROM shipments"},
        {**comparison(), "region": "North'; DROP TABLE shipments"},
        {**comparison(), "baseline_end": "2026-09-22"},
        {**comparison(), "baseline_start": "2026-09-15"},
        {**comparison(), "baseline_start": None},
        {**comparison(), "end": "2026-09-29", "baseline_start": "2026-09-13"},
    ):
        assert client.post("/api/tools/execute", json=invalid).status_code == 422


def test_empty_comparison_returns_null_rate_change_and_region_is_preserved(tmp_path: Path):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    request = {**comparison(), "region": "Midlands"}
    result = execute_tool(db, ToolRequest.model_validate(request))
    assert [r["region"] for r in result["regional_changes"]] == ["Midlands"]
    empty = {
        "name": "compare_delivery_periods",
        "start": "2026-09-07",
        "end": "2026-09-14",
        "baseline_start": "2026-08-31",
        "baseline_end": "2026-09-07",
    }
    assert (
        execute_tool(db, ToolRequest.model_validate(empty))["change"][
            "on_time_rate_change_percentage_points"
        ]
        is None
    )


def test_evidence_ids_repeat_and_change_with_request_or_source(tmp_path: Path):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    request = ToolRequest.model_validate(comparison())
    first = execute_tool(db, request)["evidence"]
    assert execute_tool(db, request)["evidence"] == first
    filtered = execute_tool(db, ToolRequest.model_validate({**comparison(), "region": "North"}))
    assert filtered["evidence"]["snapshot_id"] == first["snapshot_id"]
    assert filtered["evidence"]["evidence_id"] != first["evidence_id"]
    build_snapshot(db, rows=generate_rows(43))
    changed = execute_tool(db, request)["evidence"]
    assert changed["snapshot_id"] != first["snapshot_id"]
    assert changed["evidence_id"] != first["evidence_id"]


def test_comparison_uses_one_snapshot_when_source_is_replaced(tmp_path: Path, monkeypatch):
    import operations_assistant.tools as tools

    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    request = ToolRequest.model_validate(comparison())
    expected = execute_tool(db, request)
    original = tools.summary_from_connection
    calls = []

    def replace_between_cohorts(connection, start, end, region):
        result = original(connection, start, end, region)
        calls.append(connection)
        if len(calls) == 1:
            build_snapshot(db, rows=generate_rows(43))
        return result

    monkeypatch.setattr(tools, "summary_from_connection", replace_between_cohorts)
    observed = execute_tool(db, request)
    assert len(calls) == 2
    assert calls[0] is calls[1]
    assert observed == expected

def test_exception_tool_returns_bounded_reconciled_rows_without_mutation(
    tmp_path: Path,
):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    fingerprint = hashlib.sha256(db.read_bytes()).hexdigest()
    request = ToolRequest.model_validate(
        {
            "name": "delivery_exceptions",
            "start": "2026-09-21",
            "end": "2026-09-28",
            "limit": 5,
        }
    )

    result = execute_tool(db, request)

    assert result["exception_count"] == 65
    assert result["returned_count"] == 5
    assert result["truncated"] is True
    assert len(result["rows"]) == 5
    assert all(row["outcome"] == "overdue_open" for row in result["rows"])
    assert result["rows"] == sorted(
        result["rows"],
        key=lambda row: (
            0 if row["outcome"] == "overdue_open" else 1,
            -row["delay_minutes"],
            row["promised_at"],
            row["shipment_id"],
        ),
    )
    assert result["evidence"]["request"]["limit"] == 5

    overdue = execute_tool(
        db,
        ToolRequest.model_validate(
            {
                "name": "delivery_exceptions",
                "start": "2026-09-21",
                "end": "2026-09-28",
                "outcome": "overdue_open",
                "limit": 100,
            }
        ),
    )
    assert overdue["selected_outcome"] == "overdue_open"
    assert overdue["exception_count"] == overdue["returned_count"] == 21
    assert overdue["truncated"] is False
    assert {row["outcome"] for row in overdue["rows"]} == {"overdue_open"}
    assert overdue["evidence"]["request"]["outcome"] == "overdue_open"
    assert hashlib.sha256(db.read_bytes()).hexdigest() == fingerprint


def test_exception_tool_validates_bounds_and_rejects_comparison_fields(
    tmp_path: Path,
):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    client = TestClient(create_app(db))
    request = {
        "name": "delivery_exceptions",
        "start": "2026-09-21",
        "end": "2026-09-28",
    }

    response = client.post("/api/tools/execute", json={**request, "limit": 3})
    assert response.status_code == 200
    assert response.json()["returned_count"] == 3

    for invalid in (
        {**request, "limit": 0},
        {**request, "limit": 101},
        {**request, "baseline_start": "2026-09-14"},
        {**request, "outcome": "on_time"},
        {**request, "sql": "SELECT * FROM shipments"},
    ):
        assert client.post("/api/tools/execute", json=invalid).status_code == 422
