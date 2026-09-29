import json
from pathlib import Path

import pytest

from finance_portfolio.run_pipeline import (
    PipelineStep,
    build_steps,
    order_steps,
    run_pipeline,
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
