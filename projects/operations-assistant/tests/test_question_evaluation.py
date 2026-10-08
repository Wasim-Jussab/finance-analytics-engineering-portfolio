from pathlib import Path

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

    assert result["cases"] == result["passed"] == 8
    assert result["failed"] == 0
    assert result["answered_cases"] == result["tool_executions"] == 4
    assert result["blocked_cases"] == 4
    assert result["database_unchanged"] is True
    assert all(row["evidence_id"] for row in result["results"][:4])
    assert all(row["tool"] is None for row in result["results"][4:])


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
