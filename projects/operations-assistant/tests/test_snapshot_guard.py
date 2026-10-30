from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from operations_assistant.app import create_app
from operations_assistant.generate import build_snapshot, generate_rows


@pytest.mark.parametrize("endpoint", ["tools/execute", "answers", "questions"])
def test_snapshot_guard_rejects_replacement_before_metric_execution(
    tmp_path: Path, monkeypatch, endpoint
):
    import operations_assistant.tools as tools

    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    client = TestClient(create_app(database))
    request = {
        "start": "2026-09-21",
        "end": "2026-09-28",
        "limit": 5,
    }
    if endpoint == "questions":
        request["question"] = "List the five worst delivery exceptions"
    else:
        request["name"] = "delivery_exceptions"
    url = "/api/" + endpoint
    first = client.post(url, json=request)
    assert first.status_code == 200
    snapshot_id = first.json()["evidence"]["snapshot_id"]
    guarded = {**request, "offset": 5, "expected_snapshot_id": snapshot_id}
    matching = client.post(url, json=guarded)
    assert matching.status_code == 200
    assert matching.json()["evidence"]["request"]["expected_snapshot_id"] == snapshot_id
    assert matching.json()["evidence"]["snapshot_id"] == snapshot_id
    assert client.post(url, json={**request, "expected_snapshot_id": "bad"}).status_code == 422
    build_snapshot(database, rows=generate_rows(43))

    def should_not_execute(*args, **kwargs):
        raise AssertionError("Metrics must not execute against a mismatched snapshot")

    monkeypatch.setattr(tools, "_execute_from_connection", should_not_execute)
    rejected = client.post(url, json=guarded)
    assert rejected.status_code == 422
    assert "Snapshot changed" in str(rejected.json()["detail"])
