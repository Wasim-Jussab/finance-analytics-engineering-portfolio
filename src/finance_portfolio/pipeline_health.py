"""Summarise completed local pipeline runs from retained JSON evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median

RUN_STATUSES = {"succeeded", "failed"}
STEP_STATUSES = {"succeeded", "failed", "blocked"}
EVALUATOR_VERSION = "1.0.0"


def _sha256(path: Path) -> str:
    """Return the exact artifact fingerprint without including its local path."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _decision_evidence(report_directory: Path, policy_path: Path, result: dict) -> dict:
    """Describe the exact inputs used for a reproducible policy decision."""

    reports = [
        {"run_id": path.stem, "sha256": _sha256(path)}
        for path in sorted(report_directory.glob("*.json"))
    ]
    inputs = {
        "evaluator_version": EVALUATOR_VERSION,
        "policy_sha256": _sha256(policy_path),
        "reports": reports,
        "status": result["status"],
        "breaches": result["breaches"],
    }
    decision_id = hashlib.sha256(
        json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {"decision_id": decision_id, **inputs}


def load_policy(path: Path) -> dict:
    """Load and validate the small, versioned pipeline-health policy."""

    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read pipeline health policy {path}: {error}") from error
    required = {
        "minimum_completed_runs",
        "maximum_failure_rate",
        "require_latest_success",
        "stage_max_duration_seconds",
    }
    if not isinstance(policy, dict) or set(policy) != required:
        raise ValueError(f"Pipeline health policy must contain exactly: {sorted(required)}")
    minimum = policy["minimum_completed_runs"]
    failure_rate = policy["maximum_failure_rate"]
    durations = policy["stage_max_duration_seconds"]
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
        raise ValueError("minimum_completed_runs must be a positive integer")
    if (
        not isinstance(failure_rate, (int, float))
        or isinstance(failure_rate, bool)
        or not 0 <= failure_rate <= 1
    ):
        raise ValueError("maximum_failure_rate must be between 0 and 1")
    if not isinstance(policy["require_latest_success"], bool):
        raise ValueError("require_latest_success must be true or false")
    if not isinstance(durations, dict) or any(
        not isinstance(name, str)
        or not name
        or not isinstance(limit, (int, float))
        or isinstance(limit, bool)
        or limit <= 0
        for name, limit in durations.items()
    ):
        raise ValueError("stage_max_duration_seconds must map stage names to positive numbers")
    return policy


def evaluate_health(summary: dict, policy: dict) -> dict:
    """Evaluate completed-run evidence against explicit, non-SLO thresholds."""

    breaches = []
    if summary["total_runs"] < policy["minimum_completed_runs"]:
        breaches.append(
            {
                "check": "minimum_completed_runs",
                "observed": summary["total_runs"],
                "threshold": policy["minimum_completed_runs"],
            }
        )
    failure_rate = summary["failed_runs"] / summary["total_runs"]
    if failure_rate > policy["maximum_failure_rate"]:
        breaches.append(
            {
                "check": "maximum_failure_rate",
                "observed": round(failure_rate, 4),
                "threshold": policy["maximum_failure_rate"],
            }
        )
    if policy["require_latest_success"] and summary["latest_run"]["status"] != "succeeded":
        breaches.append(
            {
                "check": "require_latest_success",
                "observed": summary["latest_run"]["status"],
                "threshold": "succeeded",
            }
        )
    stages = {stage["name"]: stage for stage in summary["stages"]}
    for name, limit in sorted(policy["stage_max_duration_seconds"].items()):
        observed = stages.get(name, {}).get("max_duration_seconds")
        if observed is not None and observed > limit:
            breaches.append(
                {
                    "check": "stage_max_duration_seconds",
                    "stage": name,
                    "observed": observed,
                    "threshold": limit,
                }
            )
    return {
        "status": "healthy" if not breaches else "degraded",
        "breaches": breaches,
        "criteria": policy,
        "interpretation": (
            "Repository quality policy over completed-run evidence; not an availability SLO."
        ),
    }


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


def write_health_summary(
    report_directory: Path, output_path: Path, policy_path: Path | None = None
) -> dict:
    """Write a summary atomically, leaving an existing file intact on validation failure."""

    summary = build_health_decision(report_directory, policy_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return summary


def build_health_decision(
    report_directory: Path, policy_path: Path | None = None
) -> dict:
    """Build the complete deterministic summary without writing an artifact."""

    summary = build_health_summary(report_directory)
    if policy_path is not None:
        policy_result = evaluate_health(summary, load_policy(policy_path))
        summary["policy"] = policy_result
        summary["decision_evidence"] = _decision_evidence(
            report_directory, policy_path, policy_result
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, default=Path("reports/runs"))
    parser.add_argument("--output", type=Path, default=Path("reports/pipeline-health.json"))
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("config/pipeline-health-policy.json"),
    )
    arguments = parser.parse_args()
    summary = write_health_summary(arguments.reports, arguments.output, arguments.policy)
    print(
        f"Pipeline health: {summary['succeeded_runs']}/{summary['total_runs']} "
        f"completed runs succeeded; summary: {arguments.output}"
    )
    if summary["policy"]["status"] == "degraded":
        print(f"Pipeline health policy failed with {len(summary['policy']['breaches'])} breach(es)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
