from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from operations_assistant.app import create_app
from operations_assistant.generate import build_snapshot


@pytest.mark.parametrize("outcome", [None, "late_delivered", "overdue_open"])
def test_all_pages_reconcile_without_gaps_or_duplicates(tmp_path: Path, outcome):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    client = TestClient(create_app(db))
    request = {
        "name": "delivery_exceptions",
        "start": "2026-09-21",
        "end": "2026-09-28",
        "outcome": outcome,
    }
    whole_response = client.post("/api/tools/execute", json={**request, "limit": 100})
    assert whole_response.status_code == 200
    whole = whole_response.json()
    rows = []
    offset = 0
    evidence_ids = set()
    while True:
        response = client.post(
            "/api/tools/execute", json={**request, "limit": 7, "offset": offset}
        )
        assert response.status_code == 200
        page = response.json()
        assert page["exception_count"] == whole["exception_count"]
        assert page["returned_count"] == len(page["rows"])
        assert page["evidence"]["snapshot_id"] == whole["evidence"]["snapshot_id"]
        assert page["evidence"]["evidence_id"] not in evidence_ids
        evidence_ids.add(page["evidence"]["evidence_id"])
        rows.extend(page["rows"])
        if not page["has_more"]:
            assert page["next_offset"] is None
            break
        assert page["next_offset"] == offset + len(page["rows"])
        assert page["next_offset"] > offset
        offset = page["next_offset"]
        assert offset <= whole["exception_count"]
    assert rows == whole["rows"]
    assert len({row["shipment_id"] for row in rows}) == whole["exception_count"]
    beyond = client.post(
        "/api/tools/execute",
        json={**request, "limit": 7, "offset": whole["exception_count"] + 1},
    ).json()
    assert beyond["rows"] == []
    assert beyond["returned_count"] == 0
    assert beyond["has_more"] is False
    assert beyond["next_offset"] is None
    assert beyond["exception_count"] == whole["exception_count"]
