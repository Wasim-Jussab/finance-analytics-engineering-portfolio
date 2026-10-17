"""Append and verify a local hash-linked decision audit ledger."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from operations_assistant.decision_trace import verify_decision_trace

RECORD_VERSION = "1.0.0"


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def verify_decision_audit(path: Path) -> dict:
    """Verify every trace, sequence and hash link in an existing JSONL ledger."""

    if not path.is_file():
        return {"record_count": 0, "head_record_sha256": None}

    previous_sha256 = None
    record_count = 0
    with path.open(encoding="utf-8") as audit_file:
        for line_number, line in enumerate(audit_file, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Decision audit line {line_number} is not valid JSON"
                ) from error
            recorded_sha256 = record.get("record_sha256")
            payload = {
                key: value for key, value in record.items() if key != "record_sha256"
            }
            if record.get("record_version") != RECORD_VERSION:
                raise ValueError(f"Decision audit line {line_number} has unknown version")
            if record.get("sequence") != line_number:
                raise ValueError(f"Decision audit line {line_number} has invalid sequence")
            if record.get("previous_record_sha256") != previous_sha256:
                raise ValueError(f"Decision audit line {line_number} breaks the hash chain")
            if recorded_sha256 != _fingerprint(payload):
                raise ValueError(f"Decision audit line {line_number} has changed content")
            verify_decision_trace(record.get("decision_trace", {}))
            previous_sha256 = recorded_sha256
            record_count = line_number

    return {
        "record_count": record_count,
        "head_record_sha256": previous_sha256,
    }


def decision_audit_status(path: Path | None) -> dict:
    """Return integrity metadata without exposing ledger records or its path."""

    if path is None:
        return {
            "configured": False,
            "verification": "not_run",
            "record_version": RECORD_VERSION,
            "record_count": None,
            "head_record_sha256": None,
            "raw_question_retained": False,
            "storage": "local hash-linked JSONL; not immutable storage",
        }
    state = verify_decision_audit(path)
    return {
        "configured": True,
        "verification": "passed",
        "record_version": RECORD_VERSION,
        **state,
        "raw_question_retained": False,
        "storage": "local hash-linked JSONL; not immutable storage",
    }


def append_decision_audit(path: Path, decision_trace: dict) -> dict:
    """Verify existing evidence, then append one privacy-conscious decision trace."""

    verify_decision_trace(decision_trace)
    state = verify_decision_audit(path)
    payload = {
        "record_version": RECORD_VERSION,
        "sequence": state["record_count"] + 1,
        "previous_record_sha256": state["head_record_sha256"],
        "decision_trace": decision_trace,
    }
    record = {**payload, "record_sha256": _fingerprint(payload)}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        audit_file.flush()
        os.fsync(audit_file.fileno())
    return {
        "mode": "local hash-linked JSONL; not immutable storage",
        "sequence": record["sequence"],
        "record_sha256": record["record_sha256"],
        "previous_record_sha256": record["previous_record_sha256"],
    }
