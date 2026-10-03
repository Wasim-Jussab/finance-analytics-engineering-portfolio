import json
from pathlib import Path

import pytest

from finance_portfolio.run_pipeline import (
    PipelineLockedError,
    PipelineStep,
    build_steps,
    order_steps,
    pipeline_lock,
    run_pipeline,
    run_pipeline_with_lock,
)


def test_pipeline_runs_each_step_in_dependency_order(tmp_path: Path) -> None:
    steps = (
        PipelineStep("transform", ("transform",), depends_on=("load",)),
        PipelineStep("extract", ("extract",)),
        PipelineStep("load", ("load",), depends_on=("extract",)),
    )
    attempted: list[str] = []

    def succeed(step: PipelineStep, project_root: Path) -> int:
        assert project_root == tmp_path
        attempted.append(step.name)
        return 0

    report_path = tmp_path / "reports" / "run.json"
    report = run_pipeline(
        steps,
        tmp_path,
        Path("data/test.duckdb"),
        report_path,
        runner=succeed,
    )

    assert report.status == "succeeded"
    assert attempted == ["extract", "load", "transform"]
    assert [result.status for result in report.steps] == ["succeeded"] * 3
    written_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert written_report["run_id"] == report.run_id
    assert written_report["database"] == "data/test.duckdb"


def test_pipeline_stops_after_first_failure(tmp_path: Path) -> None:
    steps = (
        PipelineStep("generate", ("generate",)),
        PipelineStep("load", ("load",), depends_on=("generate",)),
        PipelineStep("build", ("build",), depends_on=("load",)),
    )
    attempted: list[str] = []

    def fail_load(step: PipelineStep, project_root: Path) -> int:
        attempted.append(step.name)
        return 3 if step.name == "load" else 0

    report = run_pipeline(
        steps,
        tmp_path,
        Path("data/test.duckdb"),
        tmp_path / "run.json",
        runner=fail_load,
    )

    assert report.status == "failed"
    assert attempted == ["generate", "load"]
    assert [result.status for result in report.steps] == [
        "succeeded",
        "failed",
        "blocked",
    ]
    assert report.steps[1].return_code == 3
    assert report.steps[2].return_code is None


def test_pipeline_definition_rejects_missing_dependencies_and_cycles() -> None:
    with pytest.raises(ValueError, match="Unknown pipeline dependencies: missing"):
        order_steps((PipelineStep("load", ("load",), depends_on=("missing",)),))

    cyclic_steps = (
        PipelineStep("first", ("first",), depends_on=("second",)),
        PipelineStep("second", ("second",), depends_on=("first",)),
    )
    with pytest.raises(ValueError, match="Pipeline dependency cycle: first, second"):
        order_steps(cyclic_steps)


def test_current_pipeline_passes_database_to_load_and_dbt() -> None:
    steps = build_steps(Path("data/example.duckdb"))

    assert [step.name for step in steps] == [
        "generate",
        "load",
        "source_freshness",
        "dbt_build",
    ]
    assert steps[1].command[-2:] == ("--database", "data/example.duckdb")
    assert dict(steps[2].environment)["FINANCE_DUCKDB_PATH"] == "data/example.duckdb"
    assert dict(steps[3].environment)["DBT_SEND_ANONYMOUS_USAGE_STATS"] == "false"


def test_pipeline_lock_rejects_a_second_run_without_changing_the_report(
    tmp_path: Path,
) -> None:
    lock_path = tmp_path / "reports" / "pipeline.lock"
    report_path = tmp_path / "reports" / "latest.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text('{"status": "succeeded"}\n', encoding="utf-8")
    attempted: list[str] = []

    def record_attempt(step: PipelineStep, project_root: Path) -> int:
        attempted.append(step.name)
        return 0

    with pipeline_lock(lock_path, "first-run", "2026-09-30T16:00:00+00:00"):
        with pytest.raises(PipelineLockedError, match="owner run first-run"):
            run_pipeline_with_lock(
                (PipelineStep("generate", ("generate",)),),
                tmp_path,
                Path("data/test.duckdb"),
                report_path,
                lock_path,
                runner=record_attempt,
            )

        assert attempted == []
        assert json.loads(report_path.read_text(encoding="utf-8")) == {"status": "succeeded"}


def test_pipeline_lock_is_released_after_success(tmp_path: Path) -> None:
    lock_path = tmp_path / "pipeline.lock"

    with pipeline_lock(lock_path, "successful-run", "2026-09-30T16:00:00+00:00"):
        metadata = json.loads(lock_path.read_text(encoding="utf-8"))
        assert metadata["run_id"] == "successful-run"
        assert metadata["process_id"] > 0

    assert not lock_path.exists()


def test_pipeline_lock_is_released_after_failure(tmp_path: Path) -> None:
    lock_path = tmp_path / "pipeline.lock"

    with pytest.raises(RuntimeError, match="controlled failure"):
        with pipeline_lock(lock_path, "failed-run", "2026-09-30T16:00:00+00:00"):
            raise RuntimeError("controlled failure")

    assert not lock_path.exists()


def test_pipeline_does_not_remove_a_lock_it_no_longer_owns(tmp_path: Path) -> None:
    lock_path = tmp_path / "pipeline.lock"

    with pipeline_lock(lock_path, "first-run", "2026-09-30T16:00:00+00:00"):
        lock_path.write_text(
            json.dumps({"run_id": "replacement-run"}) + "\n",
            encoding="utf-8",
        )

    assert json.loads(lock_path.read_text(encoding="utf-8")) == {"run_id": "replacement-run"}


def test_verification_keeps_lock_during_post_build_checks(tmp_path: Path) -> None:
    lock_path = tmp_path / "pipeline.lock"
    steps = build_steps(Path("data/example.duckdb"), verify=True)
    seen: list[str] = []

    def check_overlap(step: PipelineStep, project_root: Path) -> int:
        seen.append(step.name)
        assert lock_path.exists()
        if step.name == "incremental_payment_check":
            with pytest.raises(PipelineLockedError):
                run_pipeline_with_lock(
                    build_steps(Path("data/second.duckdb")),
                    tmp_path,
                    Path("data/second.duckdb"),
                    tmp_path / "second.json",
                    lock_path,
                    runner=lambda _step, _root: pytest.fail("overlapping run reached a stage"),
                )
        return 0

    report = run_pipeline_with_lock(
        steps,
        tmp_path,
        Path("data/example.duckdb"),
        tmp_path / "run.json",
        lock_path,
        runner=check_overlap,
    )
    assert report.status == "succeeded"
    assert seen[-3:] == ["lint", "python_tests", "dbt_docs"]
    assert not lock_path.exists()
    assert not (tmp_path / "second.json").exists()


def test_completed_runs_keep_success_and_failure_history(tmp_path: Path) -> None:
    steps = (PipelineStep("load", ("load",)),)
    latest = tmp_path / "latest.json"
    first = run_pipeline(steps, tmp_path, Path("db"), latest, runner=lambda *_: 0)
    original = (tmp_path / "runs" / f"{first.run_id}.json").read_bytes()
    second = run_pipeline(steps, tmp_path, Path("db"), latest, runner=lambda *_: 3)
    assert (tmp_path / "runs" / f"{first.run_id}.json").read_bytes() == original
    assert json.loads(original)["status"] == "succeeded"
    assert (
        json.loads((tmp_path / "runs" / f"{second.run_id}.json").read_text())["status"] == "failed"
    )
    assert json.loads(latest.read_text())["run_id"] == second.run_id


def test_archive_collision_does_not_replace_evidence_or_latest(tmp_path: Path) -> None:
    steps = (PipelineStep("load", ("load",)),)
    latest = tmp_path / "latest.json"
    run_pipeline(steps, tmp_path, Path("db"), latest, runner=lambda *_: 0, run_id="same")
    previous = latest.read_bytes()
    with pytest.raises(FileExistsError):
        run_pipeline(steps, tmp_path, Path("db"), latest, runner=lambda *_: 3, run_id="same")
    assert latest.read_bytes() == previous
    assert (tmp_path / "runs" / "same.json").read_bytes() == previous
