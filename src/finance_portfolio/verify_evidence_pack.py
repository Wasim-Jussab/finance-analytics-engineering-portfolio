"""Verify a saved evidence pack against the current local artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from finance_portfolio.evidence_pack import build_evidence_pack


def verify_evidence_pack(
    pack_path: Path,
    project_root: Path,
    latest_run_path: Path,
    run_archive_directory: Path,
    health_path: Path,
    policy_path: Path,
    manifest_path: Path,
    run_results_path: Path,
    catalog_path: Path,
) -> dict:
    """Rebuild the pack in memory and require an exact match without rewriting it."""

    try:
        recorded = json.loads(pack_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read recorded evidence pack {pack_path}: {error}") from error
    if not isinstance(recorded, dict):
        raise ValueError("Recorded evidence pack must contain a JSON object")

    expected = build_evidence_pack(
        project_root=project_root,
        latest_run_path=latest_run_path,
        run_archive_directory=run_archive_directory,
        health_path=health_path,
        policy_path=policy_path,
        manifest_path=manifest_path,
        run_results_path=run_results_path,
        catalog_path=catalog_path,
    )
    if recorded != expected:
        raise ValueError(
            "Recorded evidence pack does not match the current artifacts "
            f"(recorded pack {recorded.get('evidence_pack_id')!r}; "
            f"expected {expected['evidence_pack_id']!r})"
        )
    return recorded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=Path("reports/evidence-pack.json"))
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--latest-run", type=Path, default=Path("reports/latest-pipeline-run.json"))
    parser.add_argument("--run-archive", type=Path, default=Path("reports/runs"))
    parser.add_argument("--health", type=Path, default=Path("reports/pipeline-health.json"))
    parser.add_argument("--policy", type=Path, default=Path("config/pipeline-health-policy.json"))
    parser.add_argument("--manifest", type=Path, default=Path("target/manifest.json"))
    parser.add_argument("--run-results", type=Path, default=Path("target/run_results.json"))
    parser.add_argument("--catalog", type=Path, default=Path("target/catalog.json"))
    arguments = parser.parse_args()
    result = verify_evidence_pack(
        pack_path=arguments.pack,
        project_root=arguments.project_root,
        latest_run_path=arguments.latest_run,
        run_archive_directory=arguments.run_archive,
        health_path=arguments.health,
        policy_path=arguments.policy,
        manifest_path=arguments.manifest,
        run_results_path=arguments.run_results,
        catalog_path=arguments.catalog,
    )
    print(f"Evidence pack verified: {result['evidence_pack_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
