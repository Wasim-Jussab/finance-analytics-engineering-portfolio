"""Approved read-only tools. No free-form SQL or model inference is accepted."""

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Literal

import duckdb
from pydantic import BaseModel, ConfigDict, model_validator

from operations_assistant.metrics import summary_from_connection


class ToolRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Literal["delivery_summary", "compare_delivery_periods"]
    start: date
    end: date
    region: Literal["London", "Midlands", "North", "South"] | None = None
    baseline_start: date | None = None
    baseline_end: date | None = None

    @model_validator(mode="after")
    def validate_periods(self):
        if self.start >= self.end:
            raise ValueError("Start must precede the exclusive end")
        if self.name == "delivery_summary":
            if self.baseline_start is not None or self.baseline_end is not None:
                raise ValueError("Summary does not accept a baseline")
        else:
            if self.baseline_start is None or self.baseline_end is None:
                raise ValueError("Comparison requires both baseline dates")
            if self.baseline_start >= self.baseline_end:
                raise ValueError("Baseline start must precede its exclusive end")
            if self.baseline_end > self.start:
                raise ValueError("Baseline must finish before the current period starts")
            if self.end - self.start != self.baseline_end - self.baseline_start:
                raise ValueError("Comparison periods must have equal calendar duration")
        return self


def execute_tool(database: Path, request: ToolRequest) -> dict:
    if not database.is_file():
        raise FileNotFoundError("Generate the synthetic snapshot before starting the application")
    with duckdb.connect(str(database), read_only=True) as connection:
        connection.execute("SET TimeZone='UTC'")
        source = {
            "metadata": connection.execute("SELECT * FROM snapshot_metadata").fetchall(),
            "shipments": connection.execute(
                "SELECT * FROM shipments ORDER BY shipment_id"
            ).fetchall(),
        }
        snapshot_id = hashlib.sha256(
            json.dumps(source, sort_keys=True, default=str).encode()
        ).hexdigest()
        result = _execute_from_connection(connection, request)
    evidence = {
        "snapshot_id": snapshot_id,
        "request": request.model_dump(mode="json"),
        "result": result,
        "contract_version": "delivery-v1",
    }
    evidence_id = hashlib.sha256(
        json.dumps(evidence, sort_keys=True, default=str).encode()
    ).hexdigest()
    return {
        **result,
        "evidence": {
            "evidence_id": evidence_id,
            "snapshot_id": snapshot_id,
            "request": request.model_dump(mode="json"),
            "contract_version": "delivery-v1",
            "source": "shipments",
            "grain": "one row per shipment",
            "mode": "deterministic; model inference not implemented",
        },
    }


def _execute_from_connection(connection, request: ToolRequest) -> dict:
    current = summary_from_connection(connection, request.start, request.end, request.region)
    if request.name == "delivery_summary":
        return {"tool": request.name, "mode": "deterministic", "result": current}
    baseline = summary_from_connection(
        connection, request.baseline_start, request.baseline_end, request.region
    )

    def differences(before, after):
        old_rate, new_rate = before["on_time_rate"], after["on_time_rate"]
        return {
            "due_change": after["due"] - before["due"],
            "on_time_change": after["on_time"] - before["on_time"],
            "late_delivered_change": after["late_delivered"] - before["late_delivered"],
            "overdue_open_change": after["overdue_open"] - before["overdue_open"],
            "on_time_rate_change_percentage_points": (
                (new_rate - old_rate) * 100
                if old_rate is not None and new_rate is not None
                else None
            ),
        }

    old_regions = {r["region"]: r for r in baseline["regions"]}
    new_regions = {r["region"]: r for r in current["regions"]}
    empty = dict.fromkeys(("due", "on_time", "late_delivered", "overdue_open"), 0)
    empty["on_time_rate"] = None
    regions = [
        {
            "region": region,
            **differences(old_regions.get(region, empty), new_regions.get(region, empty)),
        }
        for region in sorted(old_regions.keys() | new_regions.keys())
    ]
    return {
        "tool": request.name,
        "mode": "deterministic",
        "baseline": baseline,
        "current": current,
        "change": differences(baseline["totals"], current["totals"]),
        "regional_changes": regions,
        "limitations": (
            "These are different promised-date cohorts in one fixed snapshot. "
            "Count differences reflect volume and outcomes; they do not establish causation "
            "or historical performance as observed at each period end."
        ),
    }
