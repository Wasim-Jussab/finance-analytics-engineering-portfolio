"""Build a reconciled index over one completed pipeline's local evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

PACK_VERSION = "1.0.0"


def _read_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(path: Path, project_root: Path) -> dict:
    try:
        relative_path = path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"Evidence artifact must be inside {project_root}: {path}") from error
    return {
        "path": relative_path,
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }


def build_evidence_pack(
    project_root: Path,
    latest_run_path: Path,
    run_archive_directory: Path,
    health_path: Path,
    policy_path: Path,
    manifest_path: Path,
    run_results_path: Path,
    catalog_path: Path,
) -> dict:
    """Reconcile related artifacts and return a deterministic evidence index."""

    latest_run = _read_object(latest_run_path, "latest pipeline run")
    run_id = latest_run.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("Latest pipeline run must contain a non-empty run_id")
    archive_path = run_archive_directory / f"{run_id}.json"
    if latest_run_path.read_bytes() != archive_path.read_bytes():
        raise ValueError("Latest pipeline pointer does not exactly match its archived run")

    health = _read_object(health_path, "pipeline health decision")
    health_latest = health.get("latest_run", {})
    if health_latest.get("run_id") != run_id:
        raise ValueError("Pipeline health latest run does not match the latest pipeline report")
    decision_evidence = health.get("decision_evidence", {})
    archived_sha = _sha256(archive_path)
    indexed_runs = {
        row.get("run_id"): row.get("sha256")
        for row in decision_evidence.get("reports", [])
        if isinstance(row, dict)
    }
    if indexed_runs.get(run_id) != archived_sha:
        raise ValueError("Pipeline health evidence does not fingerprint the latest archived run")
    if decision_evidence.get("policy_sha256") != _sha256(policy_path):
        raise ValueError("Pipeline health evidence does not match the current policy")

    manifest = _read_object(manifest_path, "dbt manifest")
    run_results = _read_object(run_results_path, "dbt run results")
    catalog = _read_object(catalog_path, "dbt catalog")
    results = run_results.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("dbt run results must contain at least one result")
    statuses = Counter(row.get("status") for row in results if isinstance(row, dict))
    unsuccessful = sorted(status for status in statuses if status not in {"pass", "success"})
    if unsuccessful:
        raise ValueError(f"dbt run results contain non-success statuses: {unsuccessful}")

    paths = (
        latest_run_path,
        archive_path,
        health_path,
        policy_path,
        manifest_path,
        run_results_path,
        catalog_path,
    )
    artifacts = [_artifact(path, project_root) for path in paths]
    payload = {
        "pack_version": PACK_VERSION,
        "pipeline_run": {
            "run_id": run_id,
            "status": latest_run.get("status"),
            "finished_at": latest_run.get("finished_at"),
        },
        "health_decision": {
            "decision_id": decision_evidence.get("decision_id"),
            "status": health.get("policy", {}).get("status"),
            "breach_count": len(health.get("policy", {}).get("breaches", [])),
        },
        "dbt_execution": {
            "invocation_id": run_results.get("metadata", {}).get("invocation_id"),
            "result_count": len(results),
            "status_counts": dict(sorted(statuses.items())),
            "manifest_node_count": len(manifest.get("nodes", {})),
            "manifest_source_count": len(manifest.get("sources", {})),
            "catalog_node_count": len(catalog.get("nodes", {})),
            "catalog_source_count": len(catalog.get("sources", {})),
        },
        "artifacts": artifacts,
        "interpretation": (
            "Reconciled local evidence index; not immutable storage, a digital signature "
            "or an availability claim."
        ),
    }
    pack_id = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {"evidence_pack_id": pack_id, **payload}


def write_evidence_pack(output_path: Path, **paths: Path) -> dict:
    """Build and atomically write the index without replacing valid evidence on failure."""

    result = build_evidence_pack(**paths)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--latest-run", type=Path, default=Path("reports/latest-pipeline-run.json"))
    parser.add_argument("--run-archive", type=Path, default=Path("reports/runs"))
    parser.add_argument("--health", type=Path, default=Path("reports/pipeline-health.json"))
    parser.add_argument("--policy", type=Path, default=Path("config/pipeline-health-policy.json"))
    parser.add_argument("--manifest", type=Path, default=Path("target/manifest.json"))
    parser.add_argument("--run-results", type=Path, default=Path("target/run_results.json"))
    parser.add_argument("--catalog", type=Path, default=Path("target/catalog.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/evidence-pack.json"))
    arguments = parser.parse_args()
    result = write_evidence_pack(
        arguments.output,
        project_root=arguments.project_root,
        latest_run_path=arguments.latest_run,
        run_archive_directory=arguments.run_archive,
        health_path=arguments.health,
        policy_path=arguments.policy,
        manifest_path=arguments.manifest,
        run_results_path=arguments.run_results,
        catalog_path=arguments.catalog,
    )
    print(
        f"Evidence pack indexed {len(result['artifacts'])} artifacts: "
        f"{result['evidence_pack_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
