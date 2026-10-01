from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from operations_assistant.app import create_app
from operations_assistant.generate import AS_OF, build_snapshot, generate_rows
from operations_assistant.metrics import summary


def row(key, delivered=None, status="In Transit", promised=None, region="North"):
    promised = promised or datetime(2026, 9, 21, 17, tzinfo=UTC)
    return (key, region, promised - timedelta(days=2), promised, delivered, status)


def test_due_denominator_keeps_late_and_open_and_excludes_cancellations(tmp_path: Path):
    promise = datetime(2026, 9, 21, 17, tzinfo=UTC)
    db = tmp_path / "ops.duckdb"
    build_snapshot(
        db,
        [
            row("on-time", promise, "Delivered"),
            row("late", promise + timedelta(hours=1), "Delivered"),
            row("open"),
            row("cancelled", status="Cancelled"),
            row("boundary", promised=datetime(2026, 9, 22, tzinfo=UTC)),
        ],
    )
    data = summary(db, date(2026, 9, 21), date(2026, 9, 22))
    assert data["totals"] == {
        "due": 3,
        "on_time": 1,
        "late_delivered": 1,
        "overdue_open": 1,
        "cancelled": 1,
        "on_time_rate": 1 / 3,
    }
    assert data["evidence"]["observed_rows"] == 4
    assert {r["shipment_id"] for r in data["exceptions"]} == {"late", "open"}


def test_empty_period_is_null_rate_and_region_cannot_change_population(tmp_path: Path):
    db = tmp_path / "ops.duckdb"
    build_snapshot(db, [row("north"), row("south", region="South")])
    result = summary(db, date(2026, 9, 21), date(2026, 9, 22), "North")
    assert result["totals"]["due"] == 1
    assert result["regions"][0]["region"] == "North"
    empty = summary(db, date(2026, 9, 1), date(2026, 9, 2))
    assert empty["totals"]["on_time_rate"] is None


def test_bad_snapshot_does_not_replace_previous_valid_snapshot(tmp_path: Path):
    db = tmp_path / "ops.duckdb"
    build_snapshot(db, [row("valid")])
    with pytest.raises(ValueError, match="unique"):
        build_snapshot(db, [row("duplicate"), row("duplicate")])
    with pytest.raises(ValueError, match="chronology"):
        build_snapshot(db, [row("future", AS_OF + timedelta(seconds=1), "Delivered")])
    assert summary(db, date(2026, 9, 21), date(2026, 9, 22))["totals"]["due"] == 1


def test_generator_is_deterministic_and_period_breakdowns_reconcile(tmp_path: Path):
    assert generate_rows() == generate_rows()
    assert generate_rows(43) != generate_rows()
    db = tmp_path / "ops.duckdb"
    assert build_snapshot(db) == 448
    data = summary(db, date(2026, 9, 14), date(2026, 9, 28))
    for key in ("due", "on_time", "late_delivered", "overdue_open", "cancelled"):
        assert sum(r[key] for r in data["regions"]) == data["totals"][key]
        assert sum(r[key] for r in data["daily"]) == data["totals"][key]


def test_api_validates_filters_and_serves_dashboard(tmp_path: Path):
    db = tmp_path / "ops.duckdb"
    build_snapshot(db)
    client = TestClient(create_app(db))
    assert client.get("/").status_code == 200
    assert "Delivery performance" in client.get("/").text
    assert client.get("/api/metrics").status_code == 200
    for query in (
        "start=2026-09-28&end=2026-09-21",
        "region=unknown",
        "region=North%27%3BDELETE%20FROM%20shipments",
        "start=2026-09-27&end=2026-09-29",
        "start=not-a-date",
    ):
        assert client.get("/api/metrics?" + query).status_code == 422
    missing = TestClient(create_app(tmp_path / "missing.duckdb"))
    assert missing.get("/api/metrics").status_code == 503
