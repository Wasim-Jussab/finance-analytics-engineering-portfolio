import hashlib
import json
from pathlib import Path

import pytest

from finance_portfolio.evidence_bundle import write_evidence_bundle
from finance_portfolio.evidence_retention import (
    build_retention_index,
    verify_retention_index,
    write_retention_index,
)


def _bundle(root: Path, suffix: str, run_id: str | None = None) -> Path:
    artifact = root / f"source-{suffix}.json"
    artifact.write_text(json.dumps({"suffix": suffix}), encoding="utf-8")
    content = artifact.read_bytes()
    payload = {
        "pack_version": "1.0.0",
        "pipeline_run": {
            "run_id": run_id or f"run-{suffix}",
            "status": "passed",
            "finished_at": f"2026-10-{10 + int(suffix):02d}T16:00:00+00:00",
        },
        "health_decision": {"decision_id": f"decision-{suffix}", "status": "healthy"},
        "dbt_execution": {"invocation_id": f"dbt-{suffix}"},
        "artifacts": [
            {
                "path": artifact.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(content).hexdigest(),
                "size_bytes": len(content),
            }
        ],
    }
    pack_id = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    pack = root / f"evidence-pack-{suffix}.json"
    pack.write_text(json.dumps({"evidence_pack_id": pack_id, **payload}), encoding="utf-8")
    write_evidence_bundle(pack, root, root / "bundles")
    return root / "bundles" / pack_id


def test_retention_index_verifies_and_summarises_all_bundles(tmp_path: Path) -> None:
    _bundle(tmp_path, "1")
    _bundle(tmp_path, "2")

    result = build_retention_index(tmp_path / "bundles")

    assert result["bundle_count"] == 2
    assert result["artifact_count"] == 2
    assert [row["pipeline_run_id"] for row in result["bundles"]] == ["run-1", "run-2"]
    assert len(result["retention_index_id"]) == 64


def test_retention_index_write_and_verify_are_deterministic(tmp_path: Path) -> None:
    _bundle(tmp_path, "1")
    output = tmp_path / "retention.json"

    first = write_retention_index(tmp_path / "bundles", output)
    second = write_retention_index(tmp_path / "bundles", output)

    assert second == first
    assert verify_retention_index(tmp_path / "bundles", output) == first


def test_retention_verifier_rejects_changed_recorded_summary(tmp_path: Path) -> None:
    _bundle(tmp_path, "1")
    output = tmp_path / "retention.json"
    write_retention_index(tmp_path / "bundles", output)
    recorded = json.loads(output.read_text(encoding="utf-8"))
    recorded["artifact_bytes"] += 1
    output.write_text(json.dumps(recorded), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match"):
        verify_retention_index(tmp_path / "bundles", output)


def test_retention_index_rejects_duplicate_run_across_different_packs(tmp_path: Path) -> None:
    _bundle(tmp_path, "1", run_id="duplicate-run")
    _bundle(tmp_path, "2", run_id="duplicate-run")

    with pytest.raises(ValueError, match="duplicate pipeline_run_id"):
        build_retention_index(tmp_path / "bundles")


def test_retention_index_rejects_tampered_bundle(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path, "1")
    (bundle / "artifacts/source-1.json").write_text("changed", encoding="utf-8")

    with pytest.raises(ValueError, match="size mismatch|fingerprint mismatch"):
        build_retention_index(tmp_path / "bundles")


def test_retention_index_rejects_unmanaged_root_file(tmp_path: Path) -> None:
    _bundle(tmp_path, "1")
    (tmp_path / "bundles/loose.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="unexpected entries"):
        build_retention_index(tmp_path / "bundles")
