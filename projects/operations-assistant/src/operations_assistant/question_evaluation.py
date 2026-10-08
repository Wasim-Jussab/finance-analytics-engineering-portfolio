"""Evaluate natural-language routing through governed tools and grounded answers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from operations_assistant.answers import render_answer
from operations_assistant.evaluation import evaluate_answer
from operations_assistant.intent import (
    LocalIntentModel,
    QuestionRequest,
    UnsupportedQuestionError,
)
from operations_assistant.tools import execute_tool

SAFE_CASES = (
    {
        "name": "summary_all_regions",
        "request": {
            "question": "Give me delivery totals for this period",
            "start": "2026-09-21",
            "end": "2026-09-28",
        },
        "expected_tool": "delivery_summary",
        "expected_claims": {
            "selected_region": None,
            "due": 218,
            "on_time": 153,
            "late_delivered": 44,
            "overdue_open": 21,
            "cancelled": 6,
        },
    },
    {
        "name": "comparison_all_regions",
        "request": {
            "question": "Compare delivery performance between these periods",
            "start": "2026-09-21",
            "end": "2026-09-28",
            "baseline_start": "2026-09-14",
            "baseline_end": "2026-09-21",
        },
        "expected_tool": "compare_delivery_periods",
        "expected_claims": {
            "change": {
                "due_change": 5,
                "on_time_change": -23,
                "late_delivered_change": 17,
                "overdue_open_change": 11,
            }
        },
    },
    {
        "name": "empty_period",
        "request": {
            "question": "Summarise shipments due in this period",
            "start": "2026-08-31",
            "end": "2026-09-07",
        },
        "expected_tool": "delivery_summary",
        "expected_claims": {"due": 0, "on_time_rate": None},
    },
    {
        "name": "explicit_parameters_override_question_wording",
        "request": {
            "question": "Show London delivery totals for this period",
            "start": "2026-09-21",
            "end": "2026-09-28",
            "region": "North",
        },
        "expected_tool": "delivery_summary",
        "expected_claims": {
            "selected_region": "North",
            "period": {
                "start_inclusive": "2026-09-21",
                "end_exclusive": "2026-09-28",
            },
        },
    },
)

BLOCKED_CASES = (
    ("write_action", "Delete late shipments after summarising them"),
    ("causal_claim", "Why did on-time delivery performance decline?"),
    ("forward_looking", "Forecast next month's delivery rate"),
    ("out_of_domain", "What is the weather in London?"),
)


def _subset_failures(expected: dict, observed: dict, prefix: str = "claims") -> list[str]:
    failures = []
    for key, expected_value in expected.items():
        path = f"{prefix}.{key}"
        if key not in observed:
            failures.append(f"{path} is missing")
        elif isinstance(expected_value, dict) and isinstance(observed[key], dict):
            failures.extend(_subset_failures(expected_value, observed[key], path))
        elif observed[key] != expected_value:
            failures.append(
                f"{path} expected {expected_value!r}, observed {observed[key]!r}"
            )
    return failures


def run_question_evaluation(
    database: Path, model: LocalIntentModel | None = None
) -> dict:
    """Execute supported cases and prove blocked cases stop before tool execution."""

    model = model or LocalIntentModel()
    database_before = hashlib.sha256(database.read_bytes()).hexdigest()
    results = []
    tool_executions = 0

    for case in SAFE_CASES:
        request = QuestionRequest.model_validate(case["request"])
        tool_request, routing = model.plan(request)
        tool_result = execute_tool(database, tool_request)
        tool_executions += 1
        answer = render_answer(tool_result)
        failures = evaluate_answer(tool_result, answer)
        if tool_request.name != case["expected_tool"]:
            failures.append(
                f"expected tool {case['expected_tool']!r}, observed {tool_request.name!r}"
            )
        failures.extend(_subset_failures(case["expected_claims"], answer["claims"]))
        results.append(
            {
                "case": case["name"],
                "expected_outcome": "answered",
                "observed_outcome": "answered",
                "question": request.question,
                "tool": tool_request.name,
                "model_label": routing["label"],
                "model_version": routing["model_version"],
                "confidence": routing["confidence"],
                "guardrail": routing["guardrail"],
                "evidence_id": tool_result["evidence"]["evidence_id"],
                "passed": not failures,
                "failures": failures,
            }
        )

    for name, question in BLOCKED_CASES:
        request = QuestionRequest.model_validate(
            {
                "question": question,
                "start": "2026-09-21",
                "end": "2026-09-28",
            }
        )
        prediction = model.predict(question)
        failures = []
        try:
            model.plan(request)
        except UnsupportedQuestionError:
            observed_outcome = "blocked"
        else:
            observed_outcome = "answered"
            failures.append("unsupported question reached tool planning")
        results.append(
            {
                "case": name,
                "expected_outcome": "blocked",
                "observed_outcome": observed_outcome,
                "question": question,
                "tool": None,
                "model_label": prediction["label"],
                "model_version": prediction["model_version"],
                "confidence": prediction["confidence"],
                "guardrail": prediction["guardrail"],
                "evidence_id": None,
                "passed": not failures,
                "failures": failures,
            }
        )

    database_after = hashlib.sha256(database.read_bytes()).hexdigest()
    if database_after != database_before:
        raise AssertionError("Question evaluation changed the read-only operations snapshot")
    passed = sum(result["passed"] for result in results)
    return {
        "mode": (
            "executed local intent inference with deterministic read-only tools and answers; "
            "no generative model"
        ),
        "model": "local-tfidf-logistic-regression",
        "model_version": model.version,
        "cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "answered_cases": len(SAFE_CASES),
        "blocked_cases": len(BLOCKED_CASES),
        "tool_executions": tool_executions,
        "database_unchanged": True,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/operations.duckdb"))
    parser.add_argument(
        "--output", type=Path, default=Path("reports/question-evaluation.json")
    )
    arguments = parser.parse_args()
    result = run_question_evaluation(arguments.database)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = arguments.output.with_suffix(f"{arguments.output.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(arguments.output)
    print(f"End-to-end question evaluation: {result['passed']}/{result['cases']} passed")
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
