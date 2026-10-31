"""Locate original-database reader failures across a locked pipeline invocation."""

import argparse
import json
from pathlib import Path

import duckdb

from finance_portfolio.run_pipeline import (
    PipelineLockedError,
    build_steps,
    execute_step,
    run_pipeline_with_lock,
)


def observe(database: Path) -> dict:
    """Check original raw data read-only; do not checkpoint, copy or repair."""
    result = {"readable": False, "wal_present": None, "loan_count": None, "error_type": None}
    try:
        result["wal_present"] = Path(f"{database}.wal").exists()
        with duckdb.connect(str(database), read_only=True) as connection:
            result["loan_count"] = connection.execute("select count(*) from raw.loans").fetchone()[
                0
            ]
        result["readable"] = True
    except (duckdb.Error, OSError) as error:
        result["error_type"] = type(error).__name__
    return result


def diagnose(
    database: Path,
    root: Path,
    report: Path,
    lock: Path,
    verify: bool = False,
    runner=execute_step,
    observer=observe,
) -> dict:
    observations = []
    loaded = False

    def traced(step, project_root):
        nonlocal loaded
        code = runner(step, project_root)
        loaded = loaded or step.name == "load"
        if loaded:
            observations.append(
                {"after_stage": step.name, "stage_return_code": code, **observer(database)}
            )
        return code

    pipeline = run_pipeline_with_lock(
        build_steps(database, verify=verify),
        root,
        database,
        report,
        lock,
        runner=traced,
    )
    failures = [row["after_stage"] for row in observations if not row["readable"]]
    return {
        "run_id": pipeline.run_id,
        "pipeline_status": pipeline.status,
        "first_unreadable_after_stage": failures[0] if failures else None,
        "observations": observations,
        "limitation": "Stage association is not root-cause proof or case-mart readiness",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/finance.duckdb"))
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("reports/reader-lifecycle.json"))
    args = parser.parse_args()
    try:
        result = diagnose(
            args.database,
            Path.cwd(),
            Path("reports/latest-pipeline-run.json"),
            Path("reports/pipeline.lock"),
            args.verify,
        )
    except PipelineLockedError:
        parser.exit(2, "Pipeline lock exists; diagnosis did not run. No lock was removed.\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(
        0
        if result["pipeline_status"] == "succeeded"
        and result["first_unreadable_after_stage"] is None
        else 1
    )


if __name__ == "__main__":
    main()
