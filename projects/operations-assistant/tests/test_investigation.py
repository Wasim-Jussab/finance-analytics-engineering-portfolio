import hashlib
from pathlib import Path

import pytest
from operations_assistant import investigation
from operations_assistant.generate import build_snapshot, generate_rows
from operations_assistant.tools import ToolRequest, execute_tool


def request(**kwargs):
    return ToolRequest.model_validate(
        {
            "name": "delivery_exceptions",
            "start": "2026-09-21",
            "end": "2026-09-28",
            "limit": 7,
            **kwargs,
        }
    )


@pytest.mark.parametrize("outcome", [None, "late_delivered", "overdue_open"])
def test_collector_reconciles_full_tool_result_and_pins_later_pages(tmp_path: Path, outcome):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    fingerprint = hashlib.sha256(db.read_bytes()).hexdigest()
    result = investigation.collect_exceptions(db, request(outcome=outcome))
    whole = execute_tool(db, request(outcome=outcome, limit=100))
    assert result["rows"] == whole["rows"]
    assert result["exception_count"] == whole["exception_count"]
    for evidence in result["page_evidence"][1:]:
        assert evidence["request"]["expected_snapshot_id"] == result["snapshot_id"]
        assert evidence["snapshot_id"] == result["snapshot_id"]
    assert hashlib.sha256(db.read_bytes()).hexdigest() == fingerprint


def test_replacement_between_pages_rejects_without_partial_result(tmp_path: Path, monkeypatch):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    real_execute = investigation.execute_tool
    calls = []

    def replace_after_first_page(database, tool_request):
        calls.append(tool_request)
        result = real_execute(database, tool_request)
        if len(calls) == 1:
            build_snapshot(db, rows=generate_rows(43))
        return result

    monkeypatch.setattr(investigation, "execute_tool", replace_after_first_page)
    with pytest.raises(ValueError, match="Snapshot changed"):
        investigation.collect_exceptions(db, request())
    assert len(calls) == 2
    assert calls[1].expected_snapshot_id is not None


def test_population_cap_rejects_before_requesting_further_pages(tmp_path: Path, monkeypatch):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    real_execute = investigation.execute_tool
    calls = []

    def count_calls(database, tool_request):
        calls.append(tool_request)
        return real_execute(database, tool_request)

    monkeypatch.setattr(investigation, "execute_tool", count_calls)
    with pytest.raises(ValueError, match="row cap"):
        investigation.collect_exceptions(db, request(), max_rows=10)
    assert len(calls) == 1


def test_collector_rejects_unsupported_start_and_cap():
    for invalid in (request(offset=5), request(name="delivery_summary", limit=None)):
        with pytest.raises(ValueError, match="offset zero"):
            investigation.collect_exceptions(Path("unused.duckdb"), invalid)
    for cap in (0, 1001):
        with pytest.raises(ValueError, match="row cap"):
            investigation.collect_exceptions(Path("unused.duckdb"), request(), max_rows=cap)


def test_empty_population_is_complete(tmp_path: Path):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    result = investigation.collect_exceptions(db, request(start="2026-09-01", end="2026-09-02"))
    assert result["exception_count"] == 0
    assert result["rows"] == []
    assert len(result["page_evidence"]) == 1


@pytest.mark.parametrize("fault", ["count", "offset", "advance", "duplicate"])
def test_inconsistent_page_contract_is_rejected(tmp_path: Path, monkeypatch, fault):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    real_execute = investigation.execute_tool

    def inconsistent_page(database, tool_request):
        result = real_execute(database, tool_request)
        if fault == "count":
            result["returned_count"] += 1
        elif fault == "offset":
            result["offset"] += 1
        elif fault == "advance":
            result["next_offset"] = result["offset"]
        elif fault == "duplicate":
            result["rows"][-1] = result["rows"][0]
        return result

    monkeypatch.setattr(investigation, "execute_tool", inconsistent_page)
    with pytest.raises(ValueError, match="Investigation"):
        investigation.collect_exceptions(db, request())
