"""Verify the portable bundle for the currently recorded evidence pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from finance_portfolio.evidence_bundle import verify_evidence_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=Path("reports/evidence-pack.json"))
    parser.add_argument("--bundle-root", type=Path, default=Path("reports/evidence-bundles"))
    arguments = parser.parse_args()
    try:
        pack = json.loads(arguments.pack.read_text(encoding="utf-8"))
        pack_id = pack["evidence_pack_id"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError(f"Could not resolve current evidence bundle: {error}") from error
    result = verify_evidence_bundle(arguments.bundle_root / pack_id)
    print(f"Evidence bundle verified: {result['evidence_pack_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
