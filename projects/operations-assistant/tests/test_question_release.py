import json
from pathlib import Path

import pytest
from operations_assistant.generate import build_snapshot
from operations_assistant.question_evaluation import run_question_evaluation
from operations_assistant.question_release import (
    build_question_release_decision,
    evaluate_question_release,
    load_question_release_policy,
)

POLICY = {
    "require_all_cases_pass": True,
    "expected_answered_cases": 4,
    "expected_blocked_cases": 4,
    "maximum_blocked_tool_executions": 0,
    "require_database_unchanged": True,
    "require_unique_decision_traces": True,
}


def _report(tmp_path: Path) -> dict:
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    return run_question_evaluation(database)


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def test_question_release_approves_executed_end_to_end_evidence(tmp_path: Path) -> None:
    result = evaluate_question_release(_report(tmp_path), POLICY)

    assert result["status"] == "approved"
    assert result["passed"] == result["cases"] == 8
    assert result["answered_cases"] == result["tool_executions"] == 4
    assert result["blocked_cases"] == 4
    assert result["blocked_tool_executions"] == 0
    assert result["verified_unique_decision_traces"] == 8
    assert result["database_unchanged"] is True
    assert result["breaches"] == []


def test_question_release_blocks_tool_execution_for_blocked_case(tmp_path: Path) -> None:
    report = _report(tmp_path)
    blocked = next(
        result for result in report["results"] if result["expected_outcome"] == "blocked"
    )
    blocked["tool"] = "delivery_summary"

    result = evaluate_question_release(report, POLICY)

    assert result["status"] == "blocked"
    assert result["blocked_tool_executions"] == 1
    assert [breach["check"] for breach in result["breaches"]] == [
        "maximum_blocked_tool_executions"
    ]


def test_question_release_rejects_inconsistent_totals(tmp_path: Path) -> None:
    report = _report(tmp_path)
    report["passed"] -= 1

    with pytest.raises(ValueError, match="totals do not reconcile"):
        evaluate_question_release(report, POLICY)


def test_question_release_fingerprints_exact_inputs(tmp_path: Path) -> None:
    evaluation = tmp_path / "evaluation.json"
    policy = tmp_path / "policy.json"
    _write(evaluation, _report(tmp_path))
    _write(policy, POLICY)
    first = build_question_release_decision(evaluation, policy)
    evaluation.write_text(evaluation.read_text(encoding="utf-8") + " ", encoding="utf-8")

    second = build_question_release_decision(evaluation, policy)

    assert first["status"] == second["status"] == "approved"
    assert first["release_evidence"]["release_id"] != second["release_evidence"]["release_id"]


def test_question_release_policy_rejects_boolean_count(tmp_path: Path) -> None:
    policy = tmp_path / "policy.json"
    _write(policy, {**POLICY, "expected_answered_cases": True})

    with pytest.raises(ValueError, match="non-negative integer"):
        load_question_release_policy(policy)
