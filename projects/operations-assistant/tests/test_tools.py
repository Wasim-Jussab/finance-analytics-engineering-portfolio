import hashlib
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from operations_assistant.app import create_app
from operations_assistant.generate import build_snapshot
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
