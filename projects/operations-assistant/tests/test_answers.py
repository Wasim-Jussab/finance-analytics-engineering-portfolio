from pathlib import Path

from fastapi.testclient import TestClient
from operations_assistant.answers import render_answer
from operations_assistant.app import create_app
from operations_assistant.evaluation import evaluate_answer, run_evaluation
from operations_assistant.generate import build_snapshot
from operations_assistant.tools import ToolRequest, execute_tool


def _comparison() -> ToolRequest:
    return ToolRequest.model_validate(
        {
            "name": "compare_delivery_periods",
            "start": "2026-09-21",
            "end": "2026-09-28",
            "baseline_start": "2026-09-14",
            "baseline_end": "2026-09-21",
        }
    )


def test_summary_answer_cites_exact_claims_and_evidence(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    request = ToolRequest.model_validate(
        {"name": "delivery_summary", "start": "2026-09-21", "end": "2026-09-28"}
    )
    tool_result = execute_tool(database, request)
    answer = render_answer(tool_result)

    assert answer["claims"]["due"] == 218
    assert answer["claims"]["on_time"] == 153
    assert tool_result["evidence"]["evidence_id"] in answer["answer"]
    assert "synthetic" in answer["answer"].lower()
    assert evaluate_answer(tool_result, answer) == []


def test_empty_summary_says_rate_is_not_calculable(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    request = ToolRequest.model_validate(
        {"name": "delivery_summary", "start": "2026-08-31", "end": "2026-09-07"}
    )
    result = render_answer(execute_tool(database, request))

    assert result["claims"]["on_time_rate"] is None
    assert "not calculable" in result["answer"]
    assert "0.00%" not in result["answer"]


def test_comparison_answer_avoids_causal_claims(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    tool_result = execute_tool(database, _comparison())
    answer = render_answer(tool_result)

    assert answer["claims"]["change"] == tool_result["change"]
    assert answer["claims"]["largest_on_time_count_decrease"]["region"] == "Midlands"
    assert evaluate_answer(tool_result, answer) == []
    assert "not a causal explanation" in answer["answer"]


def test_evaluator_detects_tampered_claim_and_evidence(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    tool_result = execute_tool(database, _comparison())
    answer = render_answer(tool_result)
    answer["claims"]["change"]["due_change"] = 999
    answer["evidence"] = {"evidence_id": "wrong"}

    failures = evaluate_answer(tool_result, answer)

    assert len(failures) == 2


def test_answer_api_and_fixed_evaluation_execute(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    client = TestClient(create_app(database))

    response = client.post("/api/answers", json=_comparison().model_dump(mode="json"))
    assert response.status_code == 200
    assert response.json()["mode"].startswith("deterministic-template")
    evaluation = run_evaluation(database)
    assert evaluation["cases"] == 4
    assert evaluation["passed"] == 4
    assert evaluation["failed"] == 0
