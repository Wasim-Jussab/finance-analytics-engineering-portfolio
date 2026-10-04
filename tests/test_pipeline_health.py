import json
from pathlib import Path

import pytest

from finance_portfolio.pipeline_health import build_health_summary, write_health_summary


def _report(run_id: str, status: str, finished: str, duration: float = 2.0) -> dict:
    failed = status == "failed"
    return {
        "run_id": run_id,
        "status": status,
        "started_at": "2026-10-04T15:00:00+00:00",
        "finished_at": finished,
        "database": "data/finance.duckdb",
        "steps": [
            {
                "name": "generate",
                "status": "succeeded",
                "command": ["generate"],
                "depends_on": [],
                "started_at": "2026-10-04T15:00:00+00:00",
                "finished_at": "2026-10-04T15:00:01+00:00",
                "duration_seconds": duration,
                "return_code": 0,
            },
            {
                "name": "load",
                "status": "failed" if failed else "succeeded",
                "command": ["load"],
                "depends_on": ["generate"],
                "started_at": "2026-10-04T15:00:01+00:00",
                "finished_at": "2026-10-04T15:00:02+00:00",
                "duration_seconds": 1.0,
                "return_code": 4 if failed else 0,
            },
            {
                "name": "dbt_build",
                "status": "blocked" if failed else "succeeded",
                "command": ["dbt", "build"],
                "depends_on": ["load"],
                "started_at": None if failed else "2026-10-04T15:00:02+00:00",
                "finished_at": None if failed else "2026-10-04T15:00:03+00:00",
                "duration_seconds": None if failed else 1.5,
                "return_code": None if failed else 0,
            },
        ],
    }


def _write(directory: Path, report: dict) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{report['run_id']}.json").write_text(json.dumps(report), encoding="utf-8")


def test_health_summary_reconciles_runs_failures_and_stage_timings(tmp_path: Path) -> None:
    reports = tmp_path / "runs"
    _write(reports, _report("first", "succeeded", "2026-10-04T15:00:03+00:00", 1.0))
    _write(reports, _report("second", "failed", "2026-10-04T16:00:03+00:00", 3.0))

    summary = build_health_summary(reports)

    assert (summary["total_runs"], summary["succeeded_runs"], summary["failed_runs"]) == (
        2,
        1,
        1,
    )
    assert summary["success_rate"] == 0.5
    assert summary["latest_run"]["run_id"] == "second"
    assert summary["failed_stage_counts"] == {"load": 1}
    stages = {stage["name"]: stage for stage in summary["stages"]}
    assert stages["generate"]["median_duration_seconds"] == 2.0
    assert stages["load"]["failed_runs"] == 1
    assert stages["dbt_build"]["blocked_runs"] == 1


def test_health_summary_rejects_filename_run_id_mismatch(tmp_path: Path) -> None:
    reports = tmp_path / "runs"
    reports.mkdir()
    (reports / "wrong.json").write_text(
        json.dumps(_report("actual", "succeeded", "2026-10-04T15:00:03+00:00")),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="does not match run_id"):
        build_health_summary(reports)


def test_health_summary_rejects_status_that_conflicts_with_steps(tmp_path: Path) -> None:
    reports = tmp_path / "runs"
    report = _report("inconsistent", "failed", "2026-10-04T15:00:03+00:00")
    report["steps"][1]["status"] = "succeeded"
    report["steps"][1]["return_code"] = 0
    report["steps"][2].update(
        status="succeeded",
        started_at="2026-10-04T15:00:02+00:00",
        finished_at="2026-10-04T15:00:03+00:00",
        duration_seconds=1.0,
        return_code=0,
    )
    _write(reports, report)

    with pytest.raises(ValueError, match="status conflicts with its steps"):
        build_health_summary(reports)


def test_failed_refresh_preserves_previous_health_summary(tmp_path: Path) -> None:
    reports = tmp_path / "runs"
    output = tmp_path / "pipeline-health.json"
    _write(reports, _report("valid", "succeeded", "2026-10-04T15:00:03+00:00"))
    write_health_summary(reports, output)
    original = output.read_bytes()
    (reports / "broken.json").write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError, match="Could not read"):
        write_health_summary(reports, output)

    assert output.read_bytes() == original
