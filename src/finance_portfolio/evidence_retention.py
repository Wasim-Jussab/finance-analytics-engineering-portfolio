"""Inventory every retained evidence bundle and verify it before indexing."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from finance_portfolio.evidence_bundle import verify_evidence_bundle

RETENTION_INDEX_VERSION = "1.0.0"


def _read_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Retained evidence pack must contain {label}")
    return value


def build_retention_index(bundle_root: Path) -> dict:
    """Verify and summarise every content-addressed bundle under one root."""

    if bundle_root.is_symlink() or not bundle_root.is_dir():
        raise ValueError(f"Evidence bundle root must be a real directory: {bundle_root}")
    bundle_paths = sorted(path for path in bundle_root.iterdir() if path.is_dir())
    unexpected = sorted(path.name for path in bundle_root.iterdir() if not path.is_dir())
    if unexpected:
        raise ValueError(f"Evidence bundle root contains unexpected entries: {unexpected}")
    if not bundle_paths:
        raise ValueError("Evidence bundle root contains no retained bundles")

    rows = []
    identity_values = {
        "pipeline_run_id": set(),
        "health_decision_id": set(),
        "dbt_invocation_id": set(),
    }
    for bundle_path in bundle_paths:
        manifest = verify_evidence_bundle(bundle_path)
        pack = _read_object(bundle_path / "evidence-pack.json", "retained evidence pack")
        identities = {
            "pipeline_run_id": _required_text(
                pack.get("pipeline_run", {}).get("run_id"), "pipeline run ID"
            ),
            "health_decision_id": _required_text(
                pack.get("health_decision", {}).get("decision_id"), "health decision ID"
            ),
            "dbt_invocation_id": _required_text(
                pack.get("dbt_execution", {}).get("invocation_id"), "dbt invocation ID"
            ),
        }
        for label, value in identities.items():
            if value in identity_values[label]:
                raise ValueError(f"Retained bundles contain duplicate {label}: {value}")
            identity_values[label].add(value)

        artifact_bytes = sum(row["size_bytes"] for row in manifest["artifacts"])
        rows.append(
            {
                "evidence_pack_id": manifest["evidence_pack_id"],
                **identities,
                "pipeline_status": pack["pipeline_run"].get("status"),
                "pipeline_finished_at": pack["pipeline_run"].get("finished_at"),
                "health_status": pack["health_decision"].get("status"),
                "artifact_count": manifest["artifact_count"],
                "artifact_bytes": artifact_bytes,
            }
        )

    rows.sort(
        key=lambda row: (
            str(row["pipeline_finished_at"]),
            row["pipeline_run_id"],
            row["evidence_pack_id"],
        )
    )
    payload = {
        "retention_index_version": RETENTION_INDEX_VERSION,
        "bundle_count": len(rows),
        "artifact_count": sum(row["artifact_count"] for row in rows),
        "artifact_bytes": sum(row["artifact_bytes"] for row in rows),
        "bundles": rows,
        "interpretation": (
            "Verified inventory of retained local bundles; not a retention policy, "
            "immutable storage, authorship proof or external attestation."
        ),
    }
    retention_index_id = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {"retention_index_id": retention_index_id, **payload}


def write_retention_index(bundle_root: Path, output_path: Path) -> dict:
    """Build and atomically write the verified retention inventory."""

    result = build_retention_index(bundle_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return result


def verify_retention_index(bundle_root: Path, index_path: Path) -> dict:
    """Rebuild the expected inventory in memory and require an exact match."""

    recorded = _read_object(index_path, "retention index")
    expected = build_retention_index(bundle_root)
    if recorded != expected:
        raise ValueError("Recorded retention index does not match retained bundles")
    return recorded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, default=Path("reports/evidence-bundles"))
    parser.add_argument("--output", type=Path, default=Path("reports/evidence-retention.json"))
    parser.add_argument("--verify", action="store_true")
    arguments = parser.parse_args()
    if arguments.verify:
        result = verify_retention_index(arguments.bundle_root, arguments.output)
        verb = "verified"
    else:
        result = write_retention_index(arguments.bundle_root, arguments.output)
        verb = "indexed"
    print(
        f"Evidence retention {verb} {result['bundle_count']} bundles: "
        f"{result['retention_index_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
