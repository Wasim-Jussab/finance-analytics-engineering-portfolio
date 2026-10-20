"""Append and verify a local hash-linked decision audit ledger."""

from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from operations_assistant.decision_trace import verify_decision_trace

RECORD_VERSION = "1.0.0"


@contextmanager
def decision_audit_write_lock(path: Path):
    """Hold one atomic local-writer lock for a decision audit ledger."""

    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(f"{path.name}.lock")
    owner_token = f"{os.getpid()}:{uuid4().hex}"
    try:
        lock_descriptor = os.open(
            lock_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError as error:
        raise ValueError(
            "Decision audit writer lock already exists; inspect it before retrying"
        ) from error

    try:
        os.write(lock_descriptor, owner_token.encode("utf-8"))
        os.fsync(lock_descriptor)
    except Exception:
        os.close(lock_descriptor)
        lock_path.unlink(missing_ok=True)
        raise

    try:
        yield
    finally:
        os.close(lock_descriptor)
        try:
            if lock_path.read_text(encoding="utf-8") == owner_token:
                lock_path.unlink()
        except FileNotFoundError:
            pass


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


def decision_audit_status(
    path: Path | None,
    expected_head_sha256: str | None = None,
    expected_record_count: int | None = None,
) -> dict:
    """Verify the ledger and optional expectations retained outside the ledger."""

    expectation_supplied = (
        expected_head_sha256 is not None or expected_record_count is not None
    )
    if expected_head_sha256 is not None and (
        len(expected_head_sha256) != 64
        or any(character not in "0123456789abcdef" for character in expected_head_sha256)
    ):
        raise ValueError(
            "Expected audit head must be 64 lowercase hexadecimal characters"
        )
    if expected_record_count is not None and expected_record_count < 0:
        raise ValueError("Expected audit record count cannot be negative")
    if path is None:
        if expectation_supplied:
            raise ValueError(
                "Cannot check an external expectation because no decision audit is configured"
            )
        return {
            "configured": False,
            "verification": "not_run",
            "record_version": RECORD_VERSION,
            "record_count": None,
            "head_record_sha256": None,
            "external_expectation_checked": False,
            "raw_question_retained": False,
            "storage": "local hash-linked JSONL; not immutable storage",
        }

    state = verify_decision_audit(path)
    if (
        expected_record_count is not None
        and state["record_count"] != expected_record_count
    ):
        raise ValueError(
            "Decision audit record count does not match the external expectation"
        )
    if (
        expected_head_sha256 is not None
        and state["head_record_sha256"] != expected_head_sha256
    ):
        raise ValueError(
            "Decision audit head fingerprint does not match the external expectation"
        )
    return {
        "configured": True,
        "verification": "passed",
        "record_version": RECORD_VERSION,
        **state,
        "external_expectation_checked": expectation_supplied,
        "raw_question_retained": False,
        "storage": "local hash-linked JSONL; not immutable storage",
    }


def append_decision_audit(path: Path, decision_trace: dict) -> dict:
    """Verify existing evidence, then append one privacy-conscious decision trace."""

    verify_decision_trace(decision_trace)
    with decision_audit_write_lock(path):
        state = verify_decision_audit(path)
        payload = {
            "record_version": RECORD_VERSION,
            "sequence": state["record_count"] + 1,
            "previous_record_sha256": state["head_record_sha256"],
            "decision_trace": decision_trace,
        }
        record = {**payload, "record_sha256": _fingerprint(payload)}
        with path.open("a", encoding="utf-8") as audit_file:
            audit_file.write(
                json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            )
            audit_file.flush()
            os.fsync(audit_file.fileno())
    return {
        "mode": "local hash-linked JSONL; not immutable storage",
        "sequence": record["sequence"],
        "record_sha256": record["record_sha256"],
        "previous_record_sha256": record["previous_record_sha256"],
    }
