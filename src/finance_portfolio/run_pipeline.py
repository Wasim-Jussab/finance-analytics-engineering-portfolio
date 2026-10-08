"""Run the local analytics pipeline as an explicit dependency graph."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
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


class PipelineLockedError(RuntimeError):
    """Raised when another invocation already owns the local pipeline lock."""


def build_steps(database: Path, verify: bool = False) -> tuple[PipelineStep, ...]:
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
    steps = (
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
    if not verify:
        return steps

    # Keep every database reader and scenario inside the same lock as ingestion.
    checks = (
        ("plan_history_check", "finance_portfolio.snapshot_history_check"),
        ("agreement_history_check", "finance_portfolio.subscription_history_check"),
        ("source_removal_check", "finance_portfolio.subscription_removal_check"),
        ("incremental_payment_check", "finance_portfolio.incremental_payment_check"),
    )
    for name, module in checks:
        steps += (
            PipelineStep(
                name,
                (sys.executable, "-m", module, "--database", str(database)),
                depends_on=(steps[-1].name,),
                environment=dbt_environment,
            ),
        )
    steps += (
        PipelineStep(
            "pipeline_health_check",
            (sys.executable, "-m", "finance_portfolio.pipeline_health_scenario"),
            depends_on=(steps[-1].name,),
        ),
        PipelineStep("lint", ("ruff", "check", "."), depends_on=(steps[-1].name,)),
        PipelineStep("python_tests", (sys.executable, "-m", "pytest"), depends_on=("lint",)),
        PipelineStep(
            "dbt_docs",
            (
                sys.executable,
                "-m",
                "finance_portfolio.generate_dbt_docs",
                "--database",
                str(database),
            ),
            depends_on=("python_tests",),
            environment=dbt_environment,
        ),
    )
    return steps


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
    # Preserve completed success/failure evidence before updating the latest pointer.
    if not report.run_id or any(
        character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        for character in report.run_id
    ):
        raise ValueError("Run ID must be safe for an archive filename")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path = report_path.parent / "runs" / f"{report.run_id}.json"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(report), indent=2) + "\n"
    # Exclusive creation rejects reuse instead of silently replacing audit evidence.
    with archive_path.open("x", encoding="utf-8") as archive:
        archive.write(payload)
        archive.flush()
        os.fsync(archive.fileno())
    temporary_path = report_path.with_suffix(f"{report_path.suffix}.tmp")
    temporary_path.write_text(
        payload,
        encoding="utf-8",
    )
    temporary_path.replace(report_path)


def _lock_metadata(run_id: str, started_at: str) -> dict[str, str | int]:
    return {
        "run_id": run_id,
        "started_at": started_at,
        "process_id": os.getpid(),
    }


@contextmanager
def pipeline_lock(lock_path: Path, run_id: str, started_at: str) -> Iterator[None]:
    """Own one atomic local lock for the duration of a pipeline invocation."""

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = _lock_metadata(run_id, started_at)
    try:
        descriptor = os.open(
            lock_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o644,
        )
    except FileExistsError as error:
        try:
            existing = json.loads(lock_path.read_text(encoding="utf-8"))
            owner = existing.get("run_id", "unknown")
            owner_started_at = existing.get("started_at", "unknown")
        except (OSError, json.JSONDecodeError, AttributeError):
            owner = "unknown"
            owner_started_at = "unknown"
        raise PipelineLockedError(
            f"Pipeline lock already exists at {lock_path}; "
            f"owner run {owner}, started {owner_started_at}"
        ) from error

    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as lock_file:
            json.dump(metadata, lock_file, indent=2)
            lock_file.write("\n")
            lock_file.flush()
            os.fsync(lock_file.fileno())
    except BaseException:
        lock_path.unlink(missing_ok=True)
        raise

    try:
        yield
    finally:
        try:
            current = json.loads(lock_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, AttributeError):
            current = {}
        if current.get("run_id") == run_id:
            lock_path.unlink(missing_ok=True)


def run_pipeline(
    steps: Sequence[PipelineStep],
    project_root: Path,
    database: Path,
    report_path: Path,
    runner: StepRunner = execute_step,
    run_id: str | None = None,
    run_started_at: str | None = None,
) -> PipelineRun:
    """Run each ready step once and stop after the first failed stage."""

    ordered_steps = order_steps(steps)
    run_id = run_id or str(uuid4())
    run_started_at = run_started_at or _timestamp()
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
        run_id=run_id,
        status="failed" if failed else "succeeded",
        started_at=run_started_at,
        finished_at=_timestamp(),
        database=str(database),
        steps=tuple(run_results),
    )
    _write_report(report, report_path)
    return report


def run_pipeline_with_lock(
    steps: Sequence[PipelineStep],
    project_root: Path,
    database: Path,
    report_path: Path,
    lock_path: Path,
    runner: StepRunner = execute_step,
) -> PipelineRun:
    """Run the pipeline only when this invocation owns the local lock."""

    run_id = str(uuid4())
    run_started_at = _timestamp()
    with pipeline_lock(lock_path, run_id, run_started_at):
        return run_pipeline(
            steps,
            project_root,
            database,
            report_path,
            runner=runner,
            run_id=run_id,
            run_started_at=run_started_at,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/finance.duckdb"))
    parser.add_argument(
        "--verify", action="store_true", help="Hold the lock through all quality checks"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/latest-pipeline-run.json"),
    )
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path("reports/pipeline.lock"),
    )
    arguments = parser.parse_args()

    project_root = Path.cwd()
    database = arguments.database
    try:
        report = run_pipeline_with_lock(
            build_steps(database, verify=arguments.verify),
            project_root,
            database,
            arguments.report,
            arguments.lock,
        )
    except PipelineLockedError as error:
        print(error, file=sys.stderr)
        return 2
    print(f"Pipeline {report.status}; run report: {arguments.report}")
    return 0 if report.status == "succeeded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
