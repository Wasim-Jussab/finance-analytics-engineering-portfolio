from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from operations_assistant.app import create_app
from operations_assistant.generate import build_snapshot
from operations_assistant.question_evaluation import run_question_evaluation


def test_question_evaluation_executes_supported_and_blocked_paths(
    tmp_path: Path,
) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)

    result = run_question_evaluation(database)

    assert result["cases"] == result["passed"] == 13
    assert result["failed"] == 0
    assert result["answered_cases"] == result["tool_executions"] == 9
    assert result["blocked_cases"] == 4
    assert result["decision_traces"] == 13
    assert result["database_unchanged"] is True
    assert all(row["evidence_id"] for row in result["results"][:9])
    assert all(row["tool"] is None for row in result["results"][9:])


def test_question_comparison_uses_only_the_selected_region(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    with TestClient(create_app(database)) as client:
        response = client.post(
            "/api/questions",
            json={
                "question": "Compare delivery performance between these periods",
                "start": "2026-09-21",
                "end": "2026-09-28",
                "baseline_start": "2026-09-14",
                "baseline_end": "2026-09-21",
                "region": "North",
            },
        )
    assert response.status_code == 200
    report = response.json()
    baseline, current = (report["claims"][key] for key in ("baseline", "current"))
    assert (baseline["due"], baseline["on_time"]) == (53, 46)
    assert (current["due"], current["on_time"]) == (54, 47)
    assert baseline["on_time_rate"] == pytest.approx(46 / 53)
    assert current["on_time_rate"] == pytest.approx(47 / 54)
    change = (47 / 54 - 46 / 53) * 100
    assert report["claims"]["change"]["on_time_rate_change_percentage_points"] == pytest.approx(
        change
    )
    assert f"{change:+.2f} percentage points" in report["answer"]
    assert report["evidence"]["request"]["region"] == "North"


def test_empty_page_does_not_erase_exception_population(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    with TestClient(create_app(database)) as client:
        response = client.post(
            "/api/questions",
            json={
                "question": "List the five worst delivery exceptions",
                "start": "2026-09-21",
                "end": "2026-09-28",
                "outcome": "overdue_open",
                "limit": 5,
                "offset": 25,
            },
        )
    assert response.status_code == 200
    report = response.json()
    assert report["claims"]["exception_count"] == 21
    assert report["claims"]["returned_count"] == 0
    assert report["claims"]["rows"] == []
    assert report["claims"]["has_more"] is False
    assert report["claims"]["next_offset"] is None
    assert "No shipment rows appear on this page." in report["answer"]
    assert "21 overdue_open shipment exceptions" in report["answer"]
    assert "earlier rows were omitted by the offset" in report["answer"]


def test_question_api_does_not_invent_rate_change_without_baseline(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    with TestClient(create_app(database)) as client:
        response = client.post(
            "/api/questions",
            json={
                "question": "Compare delivery performance between these periods",
                "start": "2026-09-14",
                "end": "2026-09-21",
                "baseline_start": "2026-09-07",
                "baseline_end": "2026-09-14",
            },
        )
    assert response.status_code == 200
    report = response.json()
    assert report["claims"]["change"]["on_time_rate_change_percentage_points"] is None
    assert "not calculable because at least one period has no due shipments" in report["answer"]


def test_explicit_parameters_remain_authoritative_over_question_wording(
    tmp_path: Path,
) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)

    result = run_question_evaluation(database)
    case = next(
        row
        for row in result["results"]
        if row["case"] == "explicit_parameters_override_question_wording"
    )

    assert case["passed"] is True
    assert case["tool"] == "delivery_summary"
    assert case["guardrail"] is None


def test_metadata_describes_actual_inference_boundary(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    client = TestClient(create_app(database))

    metadata = client.get("/api/metadata").json()

    assert metadata["mode"] == (
        "local intent inference; deterministic metrics and answers; no generative model"
    )
    assert client.get("/api/tools").json()["mode"] == (
        "deterministic read-only tools; no model invocation"
    )
