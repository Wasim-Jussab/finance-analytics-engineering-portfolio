"""Stable integrity digest for one deterministic tool result; not authentication."""

import hashlib
import json


def evidence_digest(snapshot_id: str, request: dict, result: dict, contract_version: str) -> str:
    payload = {
        "snapshot_id": snapshot_id,
        "request": request,
        "result": result,
        "contract_version": contract_version,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def investigation_digest(report: dict) -> str:
    """Canonical whole-report value digest, excluding only its own digest field."""
    payload = {key: value for key, value in report.items() if key != "report_sha256"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode()).hexdigest()
