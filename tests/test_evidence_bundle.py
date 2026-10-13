import hashlib
import json
from pathlib import Path

import pytest

from finance_portfolio.evidence_bundle import verify_evidence_bundle, write_evidence_bundle


def _write_pack(
    root: Path,
    paths: tuple[str, ...] = ("reports/run.json", "target/results.json"),
) -> Path:
    artifacts = []
    for index, relative in enumerate(paths):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"index": index}), encoding="utf-8")
        content = path.read_bytes()
        artifacts.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size_bytes": len(content),
            }
        )
    payload = {"pack_version": "1.0.0", "artifacts": artifacts}
    pack_id = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    pack = root / "reports/evidence-pack.json"
    pack.parent.mkdir(parents=True, exist_ok=True)
    pack.write_text(json.dumps({"evidence_pack_id": pack_id, **payload}), encoding="utf-8")
    return pack


def test_bundle_copies_and_verifies_exact_indexed_bytes(tmp_path: Path) -> None:
    pack = _write_pack(tmp_path)

    result = write_evidence_bundle(pack, tmp_path, tmp_path / "bundles")
    bundle = tmp_path / "bundles" / result["evidence_pack_id"]

    assert result["artifact_count"] == 2
    assert verify_evidence_bundle(bundle) == result
    assert (bundle / "artifacts/reports/run.json").read_bytes() == (
        tmp_path / "reports/run.json"
    ).read_bytes()


def test_bundle_rerun_is_idempotent(tmp_path: Path) -> None:
    pack = _write_pack(tmp_path)
    first = write_evidence_bundle(pack, tmp_path, tmp_path / "bundles")
    bundle = tmp_path / "bundles" / first["evidence_pack_id"]
    original = (bundle / "bundle-manifest.json").read_bytes()

    second = write_evidence_bundle(pack, tmp_path, tmp_path / "bundles")

    assert second == first
    assert (bundle / "bundle-manifest.json").read_bytes() == original


def test_bundle_rejects_changed_source_artifact(tmp_path: Path) -> None:
    pack = _write_pack(tmp_path)
    (tmp_path / "reports/run.json").write_text("changed", encoding="utf-8")

    with pytest.raises(ValueError, match="size does not match|fingerprint does not match"):
        write_evidence_bundle(pack, tmp_path, tmp_path / "bundles")


def test_verifier_rejects_changed_bundled_artifact(tmp_path: Path) -> None:
    pack = _write_pack(tmp_path)
    result = write_evidence_bundle(pack, tmp_path, tmp_path / "bundles")
    bundle = tmp_path / "bundles" / result["evidence_pack_id"]
    (bundle / "artifacts/target/results.json").write_text("changed", encoding="utf-8")

    with pytest.raises(ValueError, match="size mismatch|fingerprint mismatch"):
        verify_evidence_bundle(bundle)


def test_bundle_rejects_parent_path(tmp_path: Path) -> None:
    pack = _write_pack(tmp_path, ("../outside.json",))

    with pytest.raises(ValueError, match="must not escape"):
        write_evidence_bundle(pack, tmp_path, tmp_path / "bundles")


def test_verifier_rejects_unindexed_file(tmp_path: Path) -> None:
    pack = _write_pack(tmp_path)
    result = write_evidence_bundle(pack, tmp_path, tmp_path / "bundles")
    bundle = tmp_path / "bundles" / result["evidence_pack_id"]
    (bundle / "unexpected.txt").write_text("not indexed", encoding="utf-8")

    with pytest.raises(ValueError, match="missing or unexpected"):
        verify_evidence_bundle(bundle)
