"""Execute a small grounding evaluation for the deterministic answer layer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from operations_assistant.answers import render_answer
from operations_assistant.tools import ToolRequest, execute_tool

CAUSAL_PHRASES = ("because of", "caused by", "responsible for")


def _expected_claims(tool_result: dict) -> dict:
    def summary_claims(summary: dict) -> dict:
        totals = summary["totals"]
        return {
            "period": summary["period"],
            "selected_region": summary["selected_region"],
            "due": totals["due"],
            "on_time": totals["on_time"],
            "late_delivered": totals["late_delivered"],
            "overdue_open": totals["overdue_open"],
            "cancelled": totals["cancelled"],
            "on_time_rate": totals["on_time_rate"],
        }

    if tool_result["tool"] == "delivery_summary":
        return summary_claims(tool_result["result"])
    regional_decreases = [
        row for row in tool_result["regional_changes"] if row["on_time_change"] < 0
    ]
    largest = min(regional_decreases, key=lambda row: row["on_time_change"], default=None)
    return {
        "baseline": summary_claims(tool_result["baseline"]),
        "current": summary_claims(tool_result["current"]),
        "change": tool_result["change"],
        "largest_on_time_count_decrease": largest,
    }


def evaluate_answer(tool_result: dict, answer: dict) -> list[str]:
    """Return failed grounding checks without trusting the prose renderer."""

    failures = []
    evidence_id = tool_result["evidence"]["evidence_id"]
    text = answer.get("answer", "")
    if answer.get("claims") != _expected_claims(tool_result):
        failures.append("structured claims do not match the approved tool result")
    if answer.get("evidence") != tool_result["evidence"]:
        failures.append("answer evidence does not match the approved tool result")
    if evidence_id not in text:
        failures.append("answer text does not cite the evidence ID")
    if "synthetic" not in text.lower():
        failures.append("answer text does not disclose synthetic data")
    if any(phrase in text.lower() for phrase in CAUSAL_PHRASES):
        failures.append("answer text uses an unapproved causal phrase")
    if tool_result["tool"] == "delivery_summary":
        rate = tool_result["result"]["totals"]["on_time_rate"]
    else:
        rate = tool_result["change"]["on_time_rate_change_percentage_points"]
    if rate is None and "not calculable" not in text.lower():
        failures.append("null rate is not described as not calculable")
    return failures


def evaluation_requests() -> tuple[ToolRequest, ...]:
    return tuple(
        ToolRequest.model_validate(request)
        for request in (
            {
                "name": "delivery_summary",
                "start": "2026-09-21",
                "end": "2026-09-28",
            },
            {
                "name": "delivery_summary",
                "start": "2026-08-31",
                "end": "2026-09-07",
            },
            {
                "name": "compare_delivery_periods",
                "start": "2026-09-21",
                "end": "2026-09-28",
                "baseline_start": "2026-09-14",
                "baseline_end": "2026-09-21",
            },
            {
                "name": "compare_delivery_periods",
                "start": "2026-09-21",
                "end": "2026-09-28",
                "baseline_start": "2026-09-14",
                "baseline_end": "2026-09-21",
                "region": "Midlands",
            },
        )
    )


def run_evaluation(database: Path) -> dict:
    results = []
    for request in evaluation_requests():
        tool_result = execute_tool(database, request)
        answer = render_answer(tool_result)
        failures = evaluate_answer(tool_result, answer)
        results.append(
            {
                "case": request.model_dump(mode="json"),
                "evidence_id": tool_result["evidence"]["evidence_id"],
                "passed": not failures,
                "failures": failures,
            }
        )
    passed = sum(result["passed"] for result in results)
    return {
        "mode": "deterministic grounding evaluation; no model inference",
        "cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/operations.duckdb"))
    parser.add_argument("--output", type=Path, default=Path("reports/answer-evaluation.json"))
    arguments = parser.parse_args()
    result = run_evaluation(arguments.database)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = arguments.output.with_suffix(f"{arguments.output.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(arguments.output)
    print(f"Answer grounding evaluation: {result['passed']}/{result['cases']} passed")
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
