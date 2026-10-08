"""Verify a saved pipeline-health decision against its current source evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from finance_portfolio.pipeline_health import build_health_decision


def verify_health_decision(
    report_directory: Path, policy_path: Path, summary_path: Path
) -> dict:
    """Rebuild a decision in memory and require an exact match with the saved artifact."""

    try:
        recorded = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        message = f"Could not read recorded pipeline health {summary_path}: {error}"
        raise ValueError(message) from error
    if not isinstance(recorded, dict):
        raise ValueError("Recorded pipeline health must contain an object")

    expected = build_health_decision(report_directory, policy_path)
    if recorded != expected:
        recorded_id = recorded.get("decision_evidence", {}).get("decision_id")
        expected_id = expected["decision_evidence"]["decision_id"]
        raise ValueError(
            "Recorded pipeline health does not match the supplied reports and policy "
            f"(recorded decision {recorded_id!r}; expected {expected_id!r})"
        )
    return recorded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, default=Path("reports/runs"))
    parser.add_argument(
        "--policy", type=Path, default=Path("config/pipeline-health-policy.json")
    )
    parser.add_argument(
        "--summary", type=Path, default=Path("reports/pipeline-health.json")
    )
    arguments = parser.parse_args()
    result = verify_health_decision(arguments.reports, arguments.policy, arguments.summary)
    print(f"Pipeline health decision verified: {result['decision_evidence']['decision_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
