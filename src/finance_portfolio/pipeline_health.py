"""Summarise completed local pipeline runs from retained JSON evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median

RUN_STATUSES = {"succeeded", "failed"}
STEP_STATUSES = {"succeeded", "failed", "blocked"}


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO timestamp")
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed


def _validate_report(path: Path) -> dict:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read pipeline report {path.name}: {error}") from error
    if not isinstance(report, dict):
        raise ValueError(f"Pipeline report {path.name} must contain an object")
    run_id = report.get("run_id")
    if run_id != path.stem:
        raise ValueError(f"Pipeline report {path.name} does not match run_id {run_id!r}")
    status = report.get("status")
    if status not in RUN_STATUSES:
        raise ValueError(f"Pipeline report {path.name} has invalid status {status!r}")
    started = _timestamp(report.get("started_at"), "started_at")
    finished = _timestamp(report.get("finished_at"), "finished_at")
    if finished < started:
        raise ValueError(f"Pipeline report {path.name} finishes before it starts")
    steps = report.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"Pipeline report {path.name} must contain at least one step")
    names: set[str] = set()
    failed_steps = 0
    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("name"), str):
            raise ValueError(f"Pipeline report {path.name} has an invalid step")
        name = step["name"]
        if name in names:
            raise ValueError(f"Pipeline report {path.name} repeats step {name!r}")
        names.add(name)
        step_status = step.get("status")
        if step_status not in STEP_STATUSES:
            raise ValueError(f"Pipeline report {path.name} has invalid step status")
        if step_status == "blocked":
            if any(
                step.get(field) is not None
                for field in ("started_at", "finished_at", "duration_seconds", "return_code")
            ):
                raise ValueError(f"Blocked step {name!r} must not contain attempt evidence")
            continue
        step_started = _timestamp(step.get("started_at"), f"{name}.started_at")
        step_finished = _timestamp(step.get("finished_at"), f"{name}.finished_at")
        duration = step.get("duration_seconds")
        return_code = step.get("return_code")
        if step_finished < step_started or not isinstance(duration, (int, float)) or duration < 0:
            raise ValueError(f"Attempted step {name!r} has invalid timing evidence")
        if not isinstance(return_code, int):
            raise ValueError(f"Attempted step {name!r} must contain a return code")
        if (step_status == "succeeded") != (return_code == 0):
            raise ValueError(f"Step {name!r} status conflicts with its return code")
        failed_steps += step_status == "failed"
    expected_status = "failed" if failed_steps else "succeeded"
    if status != expected_status:
        raise ValueError(f"Pipeline report {path.name} status conflicts with its steps")
    return report


def build_health_summary(report_directory: Path) -> dict:
    """Validate archived reports and return a deterministic operational summary."""

    paths = sorted(report_directory.glob("*.json"))
    if not paths:
        raise ValueError(f"No archived pipeline reports found in {report_directory}")
    reports = [_validate_report(path) for path in paths]
    reports.sort(key=lambda report: _timestamp(report["finished_at"], "finished_at"))

    status_counts = Counter(report["status"] for report in reports)
    stage_records: dict[str, list[dict]] = defaultdict(list)
    failed_stage_counts: Counter[str] = Counter()
    for report in reports:
        for step in report["steps"]:
            stage_records[step["name"]].append(step)
            if step["status"] == "failed":
                failed_stage_counts[step["name"]] += 1

    stages = []
    for name in sorted(stage_records):
        records = stage_records[name]
        attempted = [record for record in records if record["status"] != "blocked"]
        durations = [record["duration_seconds"] for record in attempted]
        stages.append(
            {
                "name": name,
                "attempted_runs": len(attempted),
                "succeeded_runs": sum(r["status"] == "succeeded" for r in records),
                "failed_runs": sum(r["status"] == "failed" for r in records),
                "blocked_runs": sum(r["status"] == "blocked" for r in records),
                "median_duration_seconds": round(median(durations), 3) if durations else None,
                "max_duration_seconds": max(durations, default=None),
            }
        )

    latest = reports[-1]
    total = len(reports)
    return {
        "as_of_finished_at": latest["finished_at"],
        "total_runs": total,
        "succeeded_runs": status_counts["succeeded"],
        "failed_runs": status_counts["failed"],
        "success_rate": round(status_counts["succeeded"] / total, 4),
        "latest_run": {
            "run_id": latest["run_id"],
            "status": latest["status"],
            "started_at": latest["started_at"],
            "finished_at": latest["finished_at"],
        },
        "failed_stage_counts": dict(sorted(failed_stage_counts.items())),
        "stages": stages,
        "interpretation": (
            "Completed-run evidence only; success_rate is not a service uptime measure."
        ),
    }


def write_health_summary(report_directory: Path, output_path: Path) -> dict:
    """Write a summary atomically, leaving an existing file intact on validation failure."""

    summary = build_health_summary(report_directory)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, default=Path("reports/runs"))
    parser.add_argument("--output", type=Path, default=Path("reports/pipeline-health.json"))
    arguments = parser.parse_args()
    summary = write_health_summary(arguments.reports, arguments.output)
    print(
        f"Pipeline health: {summary['succeeded_runs']}/{summary['total_runs']} "
        f"completed runs succeeded; summary: {arguments.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
