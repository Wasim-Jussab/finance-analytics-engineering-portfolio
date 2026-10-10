"""Build stable, privacy-conscious traces for governed question decisions."""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from operations_assistant.intent import QuestionRequest
from operations_assistant.tools import ToolRequest

TRACE_VERSION = "1.0.0"


def _fingerprint(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def build_decision_trace(
    request: QuestionRequest,
    routing: dict,
    outcome: Literal["answered", "blocked"],
    tool_request: ToolRequest | None = None,
    answer: dict | None = None,
) -> dict:
    """Bind routing, parameters and evidence without retaining raw question text."""

    if outcome == "answered" and (tool_request is None or answer is None):
        raise ValueError("Answered decisions require a tool request and answer")
    if outcome == "blocked" and (tool_request is not None or answer is not None):
        raise ValueError("Blocked decisions must not contain tool or answer evidence")
    evidence = answer.get("evidence", {}) if answer else {}
    payload = {
        "trace_version": TRACE_VERSION,
        "outcome": outcome,
        "question_sha256": hashlib.sha256(request.question.encode("utf-8")).hexdigest(),
        "parameters": request.model_dump(mode="json", exclude={"question"}),
        "routing": {
            key: routing.get(key)
            for key in (
                "model",
                "model_version",
                "label",
                "confidence",
                "confidence_margin",
                "threshold",
                "guardrail",
                "accepted",
            )
        },
        "tool": tool_request.name if tool_request else None,
        "evidence_id": evidence.get("evidence_id"),
        "contract_version": evidence.get("contract_version"),
        "claims_sha256": _fingerprint(answer["claims"]) if answer else None,
        "interpretation": (
            "Deterministic decision trace; raw question text is not retained. "
            "This is not a digital signature or immutable audit log."
        ),
    }
    return {"decision_id": _fingerprint(payload), **payload}


def verify_decision_trace(trace: dict) -> None:
    """Reject a changed trace by recomputing its deterministic decision ID."""

    recorded = trace.get("decision_id")
    payload = {key: value for key, value in trace.items() if key != "decision_id"}
    expected = _fingerprint(payload)
    if recorded != expected:
        raise ValueError(
            f"Decision trace does not match its ID (recorded {recorded!r}; expected {expected!r})"
        )
