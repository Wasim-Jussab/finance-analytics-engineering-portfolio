"""Apply an explicit release policy to a verified evidence-retention index."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from finance_portfolio.evidence_retention import verify_retention_index

RELEASE_EVALUATOR_VERSION = "1.0.0"


def _read_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label.capitalize()} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_release_policy(path: Path) -> dict:
    policy = _read_object(path, "evidence release policy")
    required = {
        "minimum_retained_bundles",
        "minimum_artifacts_per_bundle",
        "allowed_pipeline_statuses",
        "allowed_health_statuses",
    }
    if set(policy) != required:
        raise ValueError(f"Evidence release policy must contain exactly: {sorted(required)}")
    for name in ("minimum_retained_bundles", "minimum_artifacts_per_bundle"):
        value = policy[name]
        if type(value) is not int or value < 1:
            raise ValueError(f"{name} must be a positive integer")
    for name in ("allowed_pipeline_statuses", "allowed_health_statuses"):
        values = policy[name]
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value for value in values)
            or len(values) != len(set(values))
        ):
            raise ValueError(f"{name} must contain unique non-empty strings")
    return policy


def evaluate_release(index: dict, policy: dict) -> dict:
    bundles = index.get("bundles")
    if not isinstance(bundles, list) or index.get("bundle_count") != len(bundles):
        raise ValueError("Retention index bundle totals do not reconcile")

    breaches = []
    if len(bundles) < policy["minimum_retained_bundles"]:
        breaches.append(
            {
                "check": "minimum_retained_bundles",
                "observed": len(bundles),
                "threshold": policy["minimum_retained_bundles"],
            }
        )
    for row in bundles:
        pack_id = row.get("evidence_pack_id")
        if row.get("artifact_count", 0) < policy["minimum_artifacts_per_bundle"]:
            breaches.append(
                {
                    "check": "minimum_artifacts_per_bundle",
                    "evidence_pack_id": pack_id,
                    "observed": row.get("artifact_count"),
                    "threshold": policy["minimum_artifacts_per_bundle"],
                }
            )
        for field, policy_field in (
            ("pipeline_status", "allowed_pipeline_statuses"),
            ("health_status", "allowed_health_statuses"),
        ):
            if row.get(field) not in policy[policy_field]:
                breaches.append(
                    {
                        "check": policy_field,
                        "evidence_pack_id": pack_id,
                        "observed": row.get(field),
                        "threshold": policy[policy_field],
                    }
                )

    return {
        "status": "approved" if not breaches else "blocked",
        "retention_index_id": index.get("retention_index_id"),
        "bundle_count": len(bundles),
        "artifact_count": index.get("artifact_count"),
        "breaches": breaches,
        "criteria": policy,
        "interpretation": (
            "Local evidence-release decision over verified retained bundles; not immutable "
            "storage, authorship proof, external attestation or production approval."
        ),
    }


def build_release_decision(bundle_root: Path, index_path: Path, policy_path: Path) -> dict:
    index = verify_retention_index(bundle_root, index_path)
    policy = load_release_policy(policy_path)
    result = evaluate_release(index, policy)
    evidence = {
        "evaluator_version": RELEASE_EVALUATOR_VERSION,
        "retention_index_sha256": _sha256(index_path),
        "policy_sha256": _sha256(policy_path),
        "status": result["status"],
        "breaches": result["breaches"],
    }
    release_decision_id = hashlib.sha256(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**result, "release_evidence": {"release_decision_id": release_decision_id, **evidence}}


def write_release_decision(
    bundle_root: Path, index_path: Path, policy_path: Path, output_path: Path
) -> dict:
    result = build_release_decision(bundle_root, index_path, policy_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return result


def verify_release_decision(
    bundle_root: Path, index_path: Path, policy_path: Path, output_path: Path
) -> dict:
    recorded = _read_object(output_path, "evidence release decision")
    expected = build_release_decision(bundle_root, index_path, policy_path)
    if recorded != expected:
        raise ValueError("Recorded evidence release decision does not match verified inputs")
    return recorded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, default=Path("reports/evidence-bundles"))
    parser.add_argument("--index", type=Path, default=Path("reports/evidence-retention.json"))
    parser.add_argument(
        "--policy", type=Path, default=Path("config/evidence-release-policy.json")
    )
    parser.add_argument("--output", type=Path, default=Path("reports/evidence-release.json"))
    parser.add_argument("--verify", action="store_true")
    arguments = parser.parse_args()
    action = verify_release_decision if arguments.verify else write_release_decision
    result = action(arguments.bundle_root, arguments.index, arguments.policy, arguments.output)
    print(
        f"Evidence release {result['status']}: {result['bundle_count']} bundles, "
        f"{result['artifact_count']} artifacts"
    )
    return 0 if result["status"] == "approved" else 1


if __name__ == "__main__":
    raise SystemExit(main())
