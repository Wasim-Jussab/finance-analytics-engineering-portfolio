"""Validate untrusted tool-call JSON before any approved read-only execution.

This boundary performs no model inference and does not execute a tool.
"""

import json

from operations_assistant.intent import QuestionRequest
from operations_assistant.tools import ToolRequest


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON field")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError("Non-finite JSON value")


def validate_proposal(raw: str, scope: QuestionRequest) -> ToolRequest:
    """Allow a proposed tool name, never model overrides of explicit caller scope."""
    if len(raw.encode("utf-8")) > 4096:
        raise ValueError("Proposal exceeds 4096 bytes")
    payload = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_invalid_constant)
    if not isinstance(payload, dict):
        raise ValueError("Proposal must be a JSON object")
    proposal = ToolRequest.model_validate(payload)
    # Rebuild the permitted request from trusted typed input. Missing fields,
    # scope changes and unsupported combinations fail rather than get corrected.
    expected = ToolRequest.model_validate(
        {
            "name": proposal.name,
            **scope.model_dump(exclude={"question"}),
        }
    )
    if proposal.model_dump() != expected.model_dump():
        raise ValueError("Proposed arguments differ from explicit caller scope")
    return proposal
