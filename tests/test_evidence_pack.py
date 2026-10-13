import hashlib
import json
from pathlib import Path

import pytest

from finance_portfolio.evidence_pack import build_evidence_pack, write_evidence_pack
from finance_portfolio.verify_evidence_pack import verify_evidence_pack


def _json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _fixture(root: Path) -> dict[str, Path]:
    run = {
        "run_id": "run-46",
        "status": "succeeded",
        "finished_at": "2026-10-09T16:00:00+00:00",
    }
    latest = root / "reports/latest-pipeline-run.json"
    archive = root / "reports/runs/run-46.json"
    _json(latest, run)
    archive.parent.mkdir(parents=True)
    archive.write_bytes(latest.read_bytes())
    policy = root / "config/pipeline-health-policy.json"
    _json(policy, {"minimum_completed_runs": 1})
    run_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    policy_sha = hashlib.sha256(policy.read_bytes()).hexdigest()
    health = root / "reports/pipeline-health.json"
    _json(
        health,
        {
            "latest_run": {"run_id": "run-46"},
            "policy": {"status": "healthy", "breaches": []},
            "decision_evidence": {
                "decision_id": "decision-46",
                "policy_sha256": policy_sha,
                "reports": [{"run_id": "run-46", "sha256": run_sha}],
            },
        },
    )
    manifest = root / "target/manifest.json"
    run_results = root / "target/run_results.json"
    catalog = root / "target/catalog.json"
    _json(manifest, {"nodes": {"model.one": {}}, "sources": {"source.one": {}}})
    _json(
        run_results,
        {
            "metadata": {"invocation_id": "dbt-46"},
            "results": [{"status": "success"}, {"status": "pass"}],
        },
    )
    _json(catalog, {"nodes": {"model.one": {}}, "sources": {"source.one": {}}})
    return {
        "project_root": root,
        "latest_run_path": latest,
        "run_archive_directory": archive.parent,
        "health_path": health,
        "policy_path": policy,
        "manifest_path": manifest,
        "run_results_path": run_results,
        "catalog_path": catalog,
    }


def test_evidence_pack_reconciles_run_health_and_dbt_artifacts(tmp_path: Path) -> None:
    result = build_evidence_pack(**_fixture(tmp_path))

    assert result["pipeline_run"] == {
        "run_id": "run-46",
        "status": "succeeded",
        "finished_at": "2026-10-09T16:00:00+00:00",
    }
    assert result["health_decision"]["decision_id"] == "decision-46"
    assert result["dbt_execution"]["status_counts"] == {"pass": 1, "success": 1}
    assert len(result["artifacts"]) == 7
    assert len(result["evidence_pack_id"]) == 64


def test_evidence_pack_rejects_changed_latest_pointer(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    _json(paths["latest_run_path"], {"run_id": "run-46", "status": "failed"})

    with pytest.raises(ValueError, match="does not exactly match"):
        build_evidence_pack(**paths)


def test_evidence_pack_rejects_non_successful_dbt_result(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    _json(paths["run_results_path"], {"results": [{"status": "error"}]})

    with pytest.raises(ValueError, match="non-success statuses"):
        build_evidence_pack(**paths)


def test_failed_refresh_preserves_existing_evidence_pack(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    output = tmp_path / "reports/evidence-pack.json"
    write_evidence_pack(output, **paths)
    original = output.read_bytes()
    paths["catalog_path"].write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError, match="Could not read dbt catalog"):
        write_evidence_pack(output, **paths)

    assert output.read_bytes() == original


def test_saved_evidence_pack_verifies_without_rewriting(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    output = tmp_path / "reports/evidence-pack.json"
    written = write_evidence_pack(output, **paths)
    original = output.read_bytes()

    verified = verify_evidence_pack(output, **paths)

    assert verified == written
    assert output.read_bytes() == original


def test_verification_rejects_changed_indexed_artifact(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    output = tmp_path / "reports/evidence-pack.json"
    write_evidence_pack(output, **paths)
    _json(paths["catalog_path"], {"nodes": {"model.changed": {}}, "sources": {}})

    with pytest.raises(ValueError, match="does not match the current artifacts"):
        verify_evidence_pack(output, **paths)


def test_verification_rejects_changed_saved_pack(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    output = tmp_path / "reports/evidence-pack.json"
    recorded = write_evidence_pack(output, **paths)
    recorded["dbt_execution"]["result_count"] = 999
    _json(output, recorded)

    with pytest.raises(ValueError, match="does not match the current artifacts"):
        verify_evidence_pack(output, **paths)
