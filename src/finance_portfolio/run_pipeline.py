"""Run the local analytics pipeline as an explicit dependency graph."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from uuid import uuid4


@dataclass(frozen=True)
class PipelineStep:
    """One executable stage and the stages that must succeed before it."""

    name: str
    command: tuple[str, ...]
    depends_on: tuple[str, ...] = ()
    environment: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class StepResult:
    """Compact operational evidence for one attempted pipeline stage."""

    name: str
    status: str
    command: tuple[str, ...]
    depends_on: tuple[str, ...]
    started_at: str | None
    finished_at: str | None
    duration_seconds: float | None
    return_code: int | None


@dataclass(frozen=True)
class PipelineRun:
    """Result of one local pipeline invocation."""

    run_id: str
    status: str
    started_at: str
    finished_at: str
    database: str
    steps: tuple[StepResult, ...]


StepRunner = Callable[[PipelineStep, Path], int]


def build_steps(database: Path) -> tuple[PipelineStep, ...]:
    """Return the current local pipeline with explicit dependencies."""

    dbt_flags = (
        "--project-dir",
        ".",
        "--profiles-dir",
        "config",
        "--target",
        "local",
        "--no-partial-parse",
    )
    dbt_environment = (
        ("FINANCE_DUCKDB_PATH", str(database)),
        ("DBT_SEND_ANONYMOUS_USAGE_STATS", "false"),
    )
    return (
        PipelineStep(
            name="generate",
            command=(sys.executable, "-m", "finance_portfolio.generate_data"),
        ),
        PipelineStep(
            name="load",
            command=(
                sys.executable,
                "-m",
                "finance_portfolio.load_duckdb",
                "--database",
                str(database),
            ),
            depends_on=("generate",),
        ),
        PipelineStep(
            name="source_freshness",
            command=("dbt", "source", "freshness", *dbt_flags),
            depends_on=("load",),
            environment=dbt_environment,
        ),
        PipelineStep(
            name="dbt_build",
            command=("dbt", "build", *dbt_flags),
            depends_on=("source_freshness",),
            environment=dbt_environment,
        ),
    )


def order_steps(steps: Sequence[PipelineStep]) -> tuple[PipelineStep, ...]:
    """Validate and topologically order a small pipeline definition."""

    step_by_name = {step.name: step for step in steps}
    if len(step_by_name) != len(steps):
        raise ValueError("Pipeline step names must be unique")

    missing = sorted(
        {
            dependency
            for step in steps
            for dependency in step.depends_on
            if dependency not in step_by_name
        }
    )
    if missing:
        raise ValueError(f"Unknown pipeline dependencies: {', '.join(missing)}")

    ordered: list[PipelineStep] = []
    completed: set[str] = set()
    while len(ordered) < len(steps):
        ready = [
            step
            for step in steps
            if step.name not in completed and set(step.depends_on) <= completed
        ]
        if not ready:
            unresolved = sorted(set(step_by_name) - completed)
            raise ValueError(f"Pipeline dependency cycle: {', '.join(unresolved)}")
        for step in ready:
            ordered.append(step)
            completed.add(step.name)
    return tuple(ordered)


def execute_step(step: PipelineStep, project_root: Path) -> int:
    """Execute one step with inherited environment and streamed output."""

    environment = os.environ.copy()
    environment.update(dict(step.environment))
    try:
        completed = subprocess.run(
            step.command,
            cwd=project_root,
            env=environment,
            check=False,
        )
    except OSError as error:
        print(f"Could not start {step.name}: {error}", file=sys.stderr)
        return 127
    return completed.returncode


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _write_report(report: PipelineRun, report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = report_path.with_suffix(f"{report_path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(asdict(report), indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(report_path)


def run_pipeline(
    steps: Sequence[PipelineStep],
    project_root: Path,
    database: Path,
    report_path: Path,
    runner: StepRunner = execute_step,
) -> PipelineRun:
    """Run each ready step once and stop after the first failed stage."""

    ordered_steps = order_steps(steps)
    run_started_at = _timestamp()
    run_results: list[StepResult] = []
    failed = False

    for step in ordered_steps:
        if failed:
            run_results.append(
                StepResult(
                    name=step.name,
                    status="blocked",
                    command=step.command,
                    depends_on=step.depends_on,
                    started_at=None,
                    finished_at=None,
                    duration_seconds=None,
                    return_code=None,
                )
            )
            continue

        step_started_at = _timestamp()
        timer_started = monotonic()
        return_code = runner(step, project_root)
        duration_seconds = round(monotonic() - timer_started, 3)
        step_status = "succeeded" if return_code == 0 else "failed"
        run_results.append(
            StepResult(
                name=step.name,
                status=step_status,
                command=step.command,
                depends_on=step.depends_on,
                started_at=step_started_at,
                finished_at=_timestamp(),
                duration_seconds=duration_seconds,
                return_code=return_code,
            )
        )
        failed = return_code != 0

    report = PipelineRun(
        run_id=str(uuid4()),
        status="failed" if failed else "succeeded",
        started_at=run_started_at,
        finished_at=_timestamp(),
        database=str(database),
        steps=tuple(run_results),
    )
    _write_report(report, report_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/finance.duckdb"))
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/latest-pipeline-run.json"),
    )
    arguments = parser.parse_args()

    project_root = Path.cwd()
    database = arguments.database
    report = run_pipeline(
        build_steps(database),
        project_root,
        database,
        arguments.report,
    )
    print(f"Pipeline {report.status}; run report: {arguments.report}")
    return 0 if report.status == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
