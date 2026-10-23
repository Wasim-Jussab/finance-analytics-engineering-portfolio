"""Render evidence-cited answers from approved deterministic tool results."""

from __future__ import annotations

from copy import deepcopy


def _rate(value: float | None) -> str:
    return "not calculable" if value is None else f"{value:.2%}"


def _period(summary: dict) -> str:
    period = summary["period"]
    return f"{period['start_inclusive']} to {period['end_exclusive']} (exclusive end)"


def _summary_claims(summary: dict) -> dict:
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


def render_answer(tool_result: dict) -> dict:
    """Return a fixed template over a governed result; no model is invoked."""

    evidence = tool_result["evidence"]
    evidence_id = evidence["evidence_id"]
    if tool_result["tool"] == "delivery_summary":
        summary = tool_result["result"]
        claims = _summary_claims(summary)
        scope = claims["selected_region"] or "all regions"
        answer = (
            f"For {scope}, {_period(summary)}, {claims['due']} non-cancelled shipments "
            f"were due: {claims['on_time']} on time, {claims['late_delivered']} delivered "
            f"late and {claims['overdue_open']} still open after promise. "
            f"The on-time completion rate is {_rate(claims['on_time_rate'])}; "
            f"{claims['cancelled']} cancelled rows are excluded from that denominator. "
            f"This uses the synthetic snapshot as of {summary['as_of']}. "
            f"Evidence: {evidence_id}."
        )
        limitations = (
            "This is a deterministic rendering of one approved metric result, not model "
            "inference or a causal explanation."
        )
    elif tool_result["tool"] == "delivery_exceptions":
        claims = {
            "period": deepcopy(tool_result["period"]),
            "selected_region": tool_result["selected_region"],
            "selected_outcome": tool_result["selected_outcome"],
            "exception_count": tool_result["exception_count"],
            "returned_count": tool_result["returned_count"],
            "limit": tool_result["limit"],
            "truncated": tool_result["truncated"],
            "rows": deepcopy(tool_result["rows"]),
        }
        scope = claims["selected_region"] or "all regions"
        outcome_scope = claims["selected_outcome"] or "late-delivered or overdue-open"
        shipment_ids = ", ".join(row["shipment_id"] for row in claims["rows"])
        truncation = (
            f" The response is truncated at the approved limit of {claims['limit']}."
            if claims["truncated"]
            else " The complete exception set is returned."
        )
        answer = (
            f"For {scope}, {tool_result['period']['start_inclusive']} to "
            f"{tool_result['period']['end_exclusive']} (exclusive end), the synthetic "
            f"snapshot contains {claims['exception_count']} {outcome_scope} "
            f"shipment exceptions. Returning {claims['returned_count']} in the governed "
            f"order: {shipment_ids}.{truncation} Snapshot as of {tool_result['as_of']}. "
            f"Evidence: {evidence_id}."
        )
        limitations = (
            "This is a deterministic rendering of bounded shipment-level evidence. "
            "It does not infer cause, treatment priority or a live operational state."
        )
    elif tool_result["tool"] == "compare_delivery_periods":
        baseline = tool_result["baseline"]
        current = tool_result["current"]
        change = tool_result["change"]
        region_changes = tool_result["regional_changes"]
        negative = [row for row in region_changes if row["on_time_change"] < 0]
        largest_decrease = (
            min(negative, key=lambda row: row["on_time_change"]) if negative else None
        )
        claims = {
            "baseline": _summary_claims(baseline),
            "current": _summary_claims(current),
            "change": deepcopy(change),
            "largest_on_time_count_decrease": deepcopy(largest_decrease),
        }
        scope = current["selected_region"] or "all regions"
        rate_change = change["on_time_rate_change_percentage_points"]
        rate_text = (
            "not calculable because at least one period has no due shipments"
            if rate_change is None
            else f"{rate_change:+.2f} percentage points"
        )
        decrease_text = (
            "No region had a decrease in on-time completion count."
            if largest_decrease is None
            else (
                f"{largest_decrease['region']} had the largest on-time count decrease "
                f"({largest_decrease['on_time_change']:+d}); this is a count contribution, "
                "not a causal explanation."
            )
        )
        answer = (
            f"For {scope}, the baseline {_period(baseline)} had "
            f"{baseline['totals']['due']} due shipments at "
            f"{_rate(baseline['totals']['on_time_rate'])}; "
            f"the current {_period(current)} had {current['totals']['due']} at "
            f"{_rate(current['totals']['on_time_rate'])}. The rate change is {rate_text}. "
            f"Due volume changed by {change['due_change']:+d}, late deliveries by "
            f"{change['late_delivered_change']:+d} and overdue-open shipments by "
            f"{change['overdue_open_change']:+d}. {decrease_text} Both periods use the "
            f"synthetic snapshot as of {current['as_of']}. Evidence: {evidence_id}."
        )
        limitations = tool_result["limitations"]
    else:
        raise ValueError(f"Unsupported approved tool result: {tool_result.get('tool')!r}")

    return {
        "mode": "deterministic-template; no generative inference",
        "answer": answer,
        "claims": claims,
        "evidence": deepcopy(evidence),
        "limitations": limitations,
    }
