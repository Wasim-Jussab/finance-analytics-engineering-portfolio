import json
from pathlib import Path

from finance_portfolio.pipeline_health_scenario import (
    EXPECTED_BREACHES,
    run_degraded_health_scenario,
)


def test_degraded_health_scenario_reconciles_expected_failure_path(
    tmp_path: Path,
) -> None:
    result = run_degraded_health_scenario(tmp_path / "scenario.json")

    assert result["status"] == "passed"
    assert result["observed_health_status"] == "degraded"
    assert result["observed_breaches"] == EXPECTED_BREACHES
    assert (result["completed_runs"], result["succeeded_runs"], result["failed_runs"]) == (
        2,
        1,
        1,
    )
    assert result["failed_stage_counts"] == {"load": 1}
    assert result["blocked_dbt_build_runs"] == 1
    assert result["decision_verified"] is True


def test_degraded_health_scenario_writes_reconciled_evidence(tmp_path: Path) -> None:
    output = tmp_path / "scenario.json"

    result = run_degraded_health_scenario(output)

    assert json.loads(output.read_text(encoding="utf-8")) == result
    assert len(result["decision_id"]) == 64
