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
