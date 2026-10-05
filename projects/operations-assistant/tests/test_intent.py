from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from operations_assistant.app import create_app
from operations_assistant.generate import build_snapshot
from operations_assistant.intent import LocalIntentModel, QuestionRequest, UnsupportedQuestionError
from operations_assistant.intent_evaluation import run_intent_evaluation


def _question(text: str, comparison: bool = False) -> dict:
    request = {
        "question": text,
        "start": "2026-09-21",
        "end": "2026-09-28",
    }
    if comparison:
        request.update(baseline_start="2026-09-14", baseline_end="2026-09-21")
    return request


def test_held_out_intent_evaluation_executes_without_failures() -> None:
    result = run_intent_evaluation()

    assert result["cases"] == 15
    assert result["passed"] == 15
    assert result["failed"] == 0


def test_local_model_abstains_from_write_and_causal_requests() -> None:
    model = LocalIntentModel()

    for text in ("Delete the delivery records", "Tell me why the driver failed"):
        with pytest.raises(UnsupportedQuestionError):
            model.plan(QuestionRequest.model_validate(_question(text)))


def test_question_api_routes_then_executes_approved_read_only_tool(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    client = TestClient(create_app(database))

    response = client.post(
        "/api/questions",
        json=_question("Compare this week's delivery performance with last week", True),
    )

    assert response.status_code == 200
    result = response.json()
    assert result["routing"]["label"] == "compare_delivery_periods"
    assert result["routing"]["model"] == "local-tfidf-logistic-regression"
    assert result["claims"]["change"]["due_change"] == 5
    assert result["evidence"]["evidence_id"] in result["answer"]


def test_question_api_rejects_missing_comparison_parameters(tmp_path: Path) -> None:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    client = TestClient(create_app(database))

    response = client.post(
        "/api/questions", json=_question("Compare this week with the previous week")
    )

    assert response.status_code == 422
    assert "Comparison requires both baseline dates" in response.json()["detail"]


def test_model_version_and_prediction_are_repeatable() -> None:
    first = LocalIntentModel()
    second = LocalIntentModel()
    question = "Show delivery performance for the selected dates"

    assert first.version == second.version
    assert first.predict(question) == second.predict(question)
