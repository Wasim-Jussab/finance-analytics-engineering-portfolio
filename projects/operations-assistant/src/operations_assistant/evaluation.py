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
    if tool_result["tool"] == "delivery_exceptions":
        return {
            "period": tool_result["period"],
            "selected_region": tool_result["selected_region"],
            "selected_outcome": tool_result["selected_outcome"],
            "exception_count": tool_result["exception_count"],
            "returned_count": tool_result["returned_count"],
            "limit": tool_result["limit"],
            "offset": tool_result["offset"],
            "has_more": tool_result["has_more"],
            "next_offset": tool_result["next_offset"],
            "truncated": tool_result["truncated"],
            "rows": tool_result["rows"],
        }
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
        scope = tool_result["result"]
    elif tool_result["tool"] == "compare_delivery_periods":
        scope = tool_result["current"]
    else:
        scope = tool_result
    region = scope["selected_region"] or "all regions"
    if not text.startswith(f"For {region}, "):
        failures.append("answer prose region does not match the approved tool result")
    if f"snapshot as of {scope['as_of']}.".lower() not in text.lower():
        failures.append("answer prose snapshot time does not match the approved tool result")
    if tool_result["tool"] == "delivery_summary":
        totals = tool_result["result"]["totals"]
        rate = totals["on_time_rate"]
        fragments = {
            "due": f"{totals['due']} non-cancelled shipments were due:",
            "on_time": f"{totals['on_time']} on time,",
            "late_delivered": f"{totals['late_delivered']} delivered late and",
            "overdue_open": f"{totals['overdue_open']} still open after promise.",
            "cancelled": f"{totals['cancelled']} cancelled rows are excluded",
            "on_time_rate": (
                "The on-time completion rate is not calculable;"
                if rate is None
                else f"The on-time completion rate is {rate:.2%};"
            ),
        }
        for claim, fragment in fragments.items():
            if fragment not in text:
                failures.append(f"summary prose {claim} does not match the approved tool result")
        if rate is None and "not calculable" not in text.lower():
            failures.append("null rate is not described as not calculable")
    elif tool_result["tool"] == "delivery_exceptions":
        region = tool_result["selected_region"] or "all regions"
        outcome = tool_result["selected_outcome"] or "late-delivered or overdue-open"
        period = tool_result["period"]
        fragments = {
            "population": (
                f"For {region}, {period['start_inclusive']} to {period['end_exclusive']} "
                f"(exclusive end), the synthetic snapshot contains "
                f"{tool_result['exception_count']} {outcome} shipment exceptions."
            ),
            "page": (
                f"Returning {tool_result['returned_count']} from offset {tool_result['offset']}"
            ),
            "rows": (
                "in the governed order: "
                + ", ".join(row["shipment_id"] for row in tool_result["rows"]) + "."
                if tool_result["rows"] else "No shipment rows appear on this page."
            ),
        }
        if tool_result["has_more"]:
            fragments["pagination"] = (
                f"Further rows remain; request offset {tool_result['next_offset']} "
                "for the next page."
            )
        elif tool_result["offset"] > 0:
            fragments["pagination"] = (
                "No further rows remain; earlier rows were omitted by the offset."
            )
        else:
            fragments["pagination"] = "The complete exception set is returned."
        for claim, fragment in fragments.items():
            if fragment not in text:
                failures.append(f"exception prose {claim} does not match the approved tool result")
    elif tool_result["tool"] == "compare_delivery_periods":
        rate = tool_result["change"]["on_time_rate_change_percentage_points"]
        for label in ("baseline", "current"):
            summary = tool_result[label]
            period, totals = summary["period"], summary["totals"]
            value = totals["on_time_rate"]
            rendered_rate = "not calculable" if value is None else f"{value:.2%}"
            scope = (
                f"{label} {period['start_inclusive']} to {period['end_exclusive']} "
                f"(exclusive end) had {totals['due']}"
            )
            expected = (
                f"{scope} due shipments at {rendered_rate};" if label == "baseline"
                else f"{scope} at {rendered_rate}."
            )
            if expected not in text:
                failures.append(f"comparison prose {label} does not match the approved tool result")
        change_text = (
            "not calculable because at least one period has no due shipments"
            if rate is None else f"{rate:+.2f} percentage points"
        )
        if f"The rate change is {change_text}." not in text:
            failures.append("comparison prose rate change does not match the approved tool result")
        change = tool_result["change"]
        volume_text = (
            f"Due volume changed by {change['due_change']:+d}, late deliveries by "
            f"{change['late_delivered_change']:+d} and overdue-open shipments by "
            f"{change['overdue_open_change']:+d}."
        )
        if volume_text not in text:
            failures.append("comparison prose volume changes do not match the approved tool result")
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
            {
                "name": "delivery_exceptions",
                "start": "2026-09-21",
                "end": "2026-09-28",
                "limit": 5,
            },
            {
                "name": "delivery_exceptions",
                "start": "2026-09-21",
                "end": "2026-09-28",
                "outcome": "overdue_open",
                "limit": 5,
                "offset": 5,
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
