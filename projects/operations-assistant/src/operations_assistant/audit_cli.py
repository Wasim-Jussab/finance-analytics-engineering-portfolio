"""Verify a local decision-audit ledger without starting the API."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from operations_assistant.decision_audit import decision_audit_status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify a local hash-linked decision-audit ledger read-only."
    )
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--expected-head-sha256")
    parser.add_argument("--expected-record-count", type=int)
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Print machine-readable integrity metadata and return a useful exit code."""

    arguments = build_parser().parse_args(argv)
    try:
        status = decision_audit_status(
            arguments.path,
            expected_head_sha256=arguments.expected_head_sha256,
            expected_record_count=arguments.expected_record_count,
        )
    except ValueError as error:
        print(
            json.dumps(
                {
                    "configured": True,
                    "verification": "failed",
                    "reason": str(error),
                    "raw_question_retained": False,
                },
                sort_keys=True,
            )
        )
        return 1

    print(json.dumps(status, sort_keys=True))
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
