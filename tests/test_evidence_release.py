import json
from pathlib import Path

import pytest

from finance_portfolio.evidence_release import (
    evaluate_release,
    load_release_policy,
    verify_release_decision,
    write_release_decision,
)
from finance_portfolio.evidence_retention import write_retention_index
from tests.test_evidence_retention import _bundle


def _policy(path: Path, minimum_bundles: int = 1) -> Path:
    path.write_text(
        json.dumps(
            {
                "minimum_retained_bundles": minimum_bundles,
                "minimum_artifacts_per_bundle": 1,
                "allowed_pipeline_statuses": ["passed"],
                "allowed_health_statuses": ["healthy"],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_release_decision_approves_verified_compliant_evidence(tmp_path: Path) -> None:
    _bundle(tmp_path, "1")
    index = tmp_path / "retention.json"
    output = tmp_path / "release.json"
    write_retention_index(tmp_path / "bundles", index)

    result = write_release_decision(
        tmp_path / "bundles", index, _policy(tmp_path / "policy.json"), output
    )

    assert result["status"] == "approved"
    assert result["breaches"] == []
    assert verify_release_decision(
        tmp_path / "bundles", index, tmp_path / "policy.json", output
    ) == result


def test_release_policy_blocks_insufficient_retained_bundles(tmp_path: Path) -> None:
    _bundle(tmp_path, "1")
    index = tmp_path / "retention.json"
    write_retention_index(tmp_path / "bundles", index)

    result = write_release_decision(
        tmp_path / "bundles", index, _policy(tmp_path / "policy.json", 2), tmp_path / "out.json"
    )

    assert result["status"] == "blocked"
    assert [breach["check"] for breach in result["breaches"]] == [
        "minimum_retained_bundles"
    ]


def test_release_policy_blocks_unapproved_statuses() -> None:
    index = {
        "retention_index_id": "index-1",
        "bundle_count": 1,
        "artifact_count": 7,
        "bundles": [
            {
                "evidence_pack_id": "pack-1",
                "artifact_count": 7,
                "pipeline_status": "failed",
                "health_status": "degraded",
            }
        ],
    }
    policy = {
        "minimum_retained_bundles": 1,
        "minimum_artifacts_per_bundle": 7,
        "allowed_pipeline_statuses": ["succeeded"],
        "allowed_health_statuses": ["healthy"],
    }

    result = evaluate_release(index, policy)

    assert result["status"] == "blocked"
    assert {breach["check"] for breach in result["breaches"]} == {
        "allowed_pipeline_statuses",
        "allowed_health_statuses",
    }


def test_release_verifier_rejects_changed_decision(tmp_path: Path) -> None:
    _bundle(tmp_path, "1")
    index = tmp_path / "retention.json"
    policy = _policy(tmp_path / "policy.json")
    output = tmp_path / "release.json"
    write_retention_index(tmp_path / "bundles", index)
    write_release_decision(tmp_path / "bundles", index, policy, output)
    recorded = json.loads(output.read_text(encoding="utf-8"))
    recorded["status"] = "blocked"
    output.write_text(json.dumps(recorded), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match"):
        verify_release_decision(tmp_path / "bundles", index, policy, output)


def test_release_policy_rejects_zero_minimum(tmp_path: Path) -> None:
    policy = _policy(tmp_path / "policy.json")
    value = json.loads(policy.read_text(encoding="utf-8"))
    value["minimum_retained_bundles"] = 0
    policy.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="positive integer"):
        load_release_policy(policy)
