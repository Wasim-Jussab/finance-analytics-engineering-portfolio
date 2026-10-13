"""Create and verify a portable snapshot of one reconciled evidence pack."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path, PurePosixPath

BUNDLE_VERSION = "1.0.0"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def _safe_path(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"{label} must not escape its evidence root: {value!r}")
    return path


def _validate_pack(pack: dict) -> str:
    pack_id = pack.get("evidence_pack_id")
    if not isinstance(pack_id, str) or len(pack_id) != 64:
        raise ValueError("Evidence pack must contain a SHA-256 evidence_pack_id")
    payload = {key: value for key, value in pack.items() if key != "evidence_pack_id"}
    expected = _sha256_bytes(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    if pack_id != expected:
        raise ValueError("Evidence pack ID does not match its recorded payload")
    return pack_id


def _validated_artifacts(pack: dict) -> list[dict]:
    artifacts = pack.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("Evidence pack must contain at least one artifact")
    validated = []
    seen: set[str] = set()
    for row in artifacts:
        if not isinstance(row, dict):
            raise ValueError("Every evidence-pack artifact must be an object")
        path = _safe_path(row.get("path"), "Artifact path").as_posix()
        if path in seen:
            raise ValueError(f"Evidence pack contains duplicate artifact path: {path}")
        sha256 = row.get("sha256")
        size_bytes = row.get("size_bytes")
        if not isinstance(sha256, str) or len(sha256) != 64:
            raise ValueError(f"Artifact {path} must contain a SHA-256 fingerprint")
        if type(size_bytes) is not int or size_bytes < 0:
            raise ValueError(f"Artifact {path} must contain a non-negative byte size")
        seen.add(path)
        validated.append({"path": path, "sha256": sha256, "size_bytes": size_bytes})
    return validated


def write_evidence_bundle(pack_path: Path, project_root: Path, bundle_root: Path) -> dict:
    """Copy exact indexed bytes into an atomic content-addressed directory."""

    pack_bytes = pack_path.read_bytes()
    pack = _read_object(pack_path, "evidence pack")
    pack_id = _validate_pack(pack)
    artifacts = _validated_artifacts(pack)
    destination = bundle_root / pack_id
    if destination.exists():
        return verify_evidence_bundle(destination)

    bundle_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{pack_id}.", dir=bundle_root) as temporary:
        staging = Path(temporary)
        (staging / "evidence-pack.json").write_bytes(pack_bytes)
        manifest_artifacts = []
        for artifact in artifacts:
            source = project_root / artifact["path"]
            try:
                source.resolve().relative_to(project_root.resolve())
            except ValueError as error:
                raise ValueError(f"Artifact escapes project root: {artifact['path']}") from error
            try:
                source_bytes = source.read_bytes()
            except OSError as error:
                raise ValueError(f"Could not read indexed artifact {source}: {error}") from error
            if len(source_bytes) != artifact["size_bytes"]:
                raise ValueError(f"Indexed size does not match artifact: {artifact['path']}")
            if _sha256_bytes(source_bytes) != artifact["sha256"]:
                raise ValueError(f"Indexed fingerprint does not match artifact: {artifact['path']}")
            bundle_path = PurePosixPath("artifacts") / artifact["path"]
            target = staging.joinpath(*bundle_path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source_bytes)
            manifest_artifacts.append(
                {
                    "source_path": artifact["path"],
                    "bundle_path": bundle_path.as_posix(),
                    "sha256": artifact["sha256"],
                    "size_bytes": artifact["size_bytes"],
                }
            )

        manifest = {
            "bundle_version": BUNDLE_VERSION,
            "evidence_pack_id": pack_id,
            "evidence_pack_sha256": _sha256_bytes(pack_bytes),
            "artifact_count": len(manifest_artifacts),
            "artifacts": manifest_artifacts,
            "interpretation": (
                "Portable local snapshot of exact indexed bytes; not immutable storage, "
                "a digital signature or external attestation."
            ),
        }
        (staging / "bundle-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        os.rename(staging, destination)
    return verify_evidence_bundle(destination)


def verify_evidence_bundle(bundle_path: Path) -> dict:
    """Verify the pack, manifest, copied bytes and exact file inventory read-only."""

    if bundle_path.is_symlink() or not bundle_path.is_dir():
        raise ValueError(f"Evidence bundle must be a real directory: {bundle_path}")
    manifest = _read_object(bundle_path / "bundle-manifest.json", "bundle manifest")
    pack_path = bundle_path / "evidence-pack.json"
    pack_bytes = pack_path.read_bytes()
    pack = _read_object(pack_path, "bundled evidence pack")
    pack_id = _validate_pack(pack)
    if bundle_path.name != pack_id or manifest.get("evidence_pack_id") != pack_id:
        raise ValueError("Bundle directory, manifest and evidence-pack IDs do not match")
    if manifest.get("evidence_pack_sha256") != _sha256_bytes(pack_bytes):
        raise ValueError("Bundled evidence-pack fingerprint does not match the manifest")

    pack_artifacts = {row["path"]: row for row in _validated_artifacts(pack)}
    rows = manifest.get("artifacts")
    if not isinstance(rows, list) or manifest.get("artifact_count") != len(rows):
        raise ValueError("Bundle manifest artifact count is inconsistent")
    expected_files = {"bundle-manifest.json", "evidence-pack.json"}
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Every bundle-manifest artifact must be an object")
        source_path = _safe_path(row.get("source_path"), "Source path").as_posix()
        bundle_relative = _safe_path(row.get("bundle_path"), "Bundle path")
        if bundle_relative.parts[0] != "artifacts":
            raise ValueError("Bundled artifacts must be stored below artifacts/")
        if source_path in seen or source_path not in pack_artifacts:
            raise ValueError(f"Bundle manifest has an unexpected artifact: {source_path}")
        expected = pack_artifacts[source_path]
        if (
            row.get("sha256") != expected["sha256"]
            or row.get("size_bytes") != expected["size_bytes"]
        ):
            raise ValueError(f"Bundle manifest disagrees with evidence pack: {source_path}")
        artifact_path = bundle_path.joinpath(*bundle_relative.parts)
        if artifact_path.is_symlink():
            raise ValueError(f"Bundled artifact must not be a symlink: {bundle_relative}")
        artifact_bytes = artifact_path.read_bytes()
        if len(artifact_bytes) != expected["size_bytes"]:
            raise ValueError(f"Bundled artifact size mismatch: {source_path}")
        if _sha256_bytes(artifact_bytes) != expected["sha256"]:
            raise ValueError(f"Bundled artifact fingerprint mismatch: {source_path}")
        expected_files.add(bundle_relative.as_posix())
        seen.add(source_path)
    if seen != set(pack_artifacts):
        raise ValueError("Bundle manifest does not cover every evidence-pack artifact")

    actual_files = {
        path.relative_to(bundle_path).as_posix()
        for path in bundle_path.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if actual_files != expected_files:
        raise ValueError("Evidence bundle contains missing or unexpected files")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=Path("reports/evidence-pack.json"))
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--bundle-root", type=Path, default=Path("reports/evidence-bundles"))
    arguments = parser.parse_args()
    result = write_evidence_bundle(arguments.pack, arguments.project_root, arguments.bundle_root)
    print(
        f"Evidence bundle wrote {result['artifact_count']} artifacts: "
        f"{result['evidence_pack_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
