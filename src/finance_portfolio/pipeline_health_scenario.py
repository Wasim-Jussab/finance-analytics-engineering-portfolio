"""Exercise the degraded pipeline-health path with isolated synthetic evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from finance_portfolio.pipeline_health import write_health_summary
from finance_portfolio.verify_pipeline_health import verify_health_decision

EXPECTED_BREACHES = [
    "minimum_completed_runs",
    "maximum_failure_rate",
    "require_latest_success",
    "stage_max_duration_seconds",
]


def _step(
    name: str,
    status: str,
    depends_on: list[str],
    started_at: str | None,
    finished_at: str | None,
    duration_seconds: float | None,
    return_code: int | None,
) -> dict:
    return {
        "name": name,
        "status": status,
        "command": [name],
        "depends_on": depends_on,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "return_code": return_code,
    }


def _report(run_id: str, status: str, hour: int, generate_duration: float) -> dict:
    prefix = f"2026-10-08T{hour:02d}:00"
    failed = status == "failed"
    return {
        "run_id": run_id,
        "status": status,
        "started_at": f"{prefix}:00+00:00",
        "finished_at": f"{prefix}:04+00:00",
        "database": "synthetic-pipeline-health-scenario",
        "steps": [
            _step(
                "generate",
                "succeeded",
                [],
                f"{prefix}:00+00:00",
                f"{prefix}:01+00:00",
                generate_duration,
                0,
            ),
            _step(
                "load",
                "failed" if failed else "succeeded",
                ["generate"],
                f"{prefix}:01+00:00",
                f"{prefix}:02+00:00",
                1.0,
                4 if failed else 0,
            ),
            _step(
                "dbt_build",
                "blocked" if failed else "succeeded",
                ["load"],
                None if failed else f"{prefix}:02+00:00",
                None if failed else f"{prefix}:04+00:00",
                None if failed else 2.0,
                None if failed else 0,
            ),
        ],
    }


def run_degraded_health_scenario(output_path: Path) -> dict:
    """Create, verify and reconcile an expected degraded decision in isolation."""

    with TemporaryDirectory(prefix="pipeline-health-scenario-") as temporary:
        workspace = Path(temporary)
        reports = workspace / "runs"
        reports.mkdir()
        policy_path = workspace / "policy.json"
        summary_path = workspace / "pipeline-health.json"

        for report in (
            _report("successful-run", "succeeded", 14, 1.0),
            _report("failed-run", "failed", 15, 3.0),
        ):
            path = reports / f"{report['run_id']}.json"
            path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        policy_path.write_text(
            json.dumps(
                {
                    "minimum_completed_runs": 3,
                    "maximum_failure_rate": 0.25,
                    "require_latest_success": True,
                    "stage_max_duration_seconds": {"generate": 2.0},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        decision = write_health_summary(reports, summary_path, policy_path)
        verified = verify_health_decision(reports, policy_path, summary_path)
        observed_breaches = [
            breach["check"] for breach in decision["policy"]["breaches"]
        ]
        stages = {stage["name"]: stage for stage in decision["stages"]}
        if decision != verified:
            raise AssertionError("Degraded decision did not pass independent verification")
        if decision["policy"]["status"] != "degraded":
            raise AssertionError("Scenario did not produce the expected degraded status")
        if observed_breaches != EXPECTED_BREACHES:
            raise AssertionError(f"Unexpected policy breaches: {observed_breaches}")
        if decision["failed_stage_counts"] != {"load": 1}:
            raise AssertionError("Failed-stage counts did not reconcile")
        if stages["dbt_build"]["blocked_runs"] != 1:
            raise AssertionError("Blocked downstream stage did not reconcile")

        result = {
            "mode": "isolated synthetic degraded-path scenario",
            "status": "passed",
            "observed_health_status": decision["policy"]["status"],
            "completed_runs": decision["total_runs"],
            "succeeded_runs": decision["succeeded_runs"],
            "failed_runs": decision["failed_runs"],
            "failed_stage_counts": decision["failed_stage_counts"],
            "blocked_dbt_build_runs": stages["dbt_build"]["blocked_runs"],
            "observed_breaches": observed_breaches,
            "decision_id": decision["decision_evidence"]["decision_id"],
            "decision_verified": True,
            "interpretation": (
                "Expected-failure scenario only; it does not measure service availability."
            ),
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_output = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary_output.replace(output_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("reports/pipeline-health-scenario.json")
    )
    arguments = parser.parse_args()
    result = run_degraded_health_scenario(arguments.output)
    print(
        f"Pipeline health degraded-path scenario: {result['status']}; "
        f"{len(result['observed_breaches'])} expected breaches verified"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
