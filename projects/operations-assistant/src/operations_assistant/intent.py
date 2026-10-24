"""A small local model that routes questions to approved read-only tools."""

from __future__ import annotations

import math
import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from operations_assistant.model_adapter import IntentModelAdapter, TfidfLogisticIntentAdapter
from operations_assistant.tools import ToolRequest

BLOCKED_PATTERNS = {
    "write_action": re.compile(
        r"\b(delete|drop|truncate|update|insert|email|send|notify)\b|"
        r"\bmark\b.+\bas\b|\bchange\b.+\b(status|date)\b",
        re.IGNORECASE,
    ),
    "causal_claim": re.compile(r"\b(why|root cause|who is to blame|caused by)\b", re.IGNORECASE),
    "forward_looking": re.compile(
        r"\b(forecast|predict|prediction|next month|next quarter|future)\b",
        re.IGNORECASE,
    ),
}
DOMAIN_PATTERN = re.compile(
    r"\b(deliver(?:y|ies|ed)?|shipment(?:s)?|order(?:s)?|parcel(?:s)?|"
    r"on[ -]?time|late|overdue|completion|promis(?:e|ed)|performance|outcomes?|"
    r"rates?|counts?|totals?)\b",
    re.IGNORECASE,
)
COMPARISON_CONTEXT_PATTERN = re.compile(
    r"\b(compare|comparison|contrast)\b.*\b(week|period|baseline)\b|"
    r"\b(week|period)\b.*\b(compare|previous|prior|baseline)\b",
    re.IGNORECASE,
)


class QuestionRequest(BaseModel):
    """Natural-language intent plus governed, explicit metric parameters."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=5, max_length=500)
    start: date
    end: date
    region: Literal["London", "Midlands", "North", "South"] | None = None
    outcome: Literal["late_delivered", "overdue_open"] | None = None
    baseline_start: date | None = None
    baseline_end: date | None = None
    limit: int | None = Field(default=None, ge=1, le=100)
    offset: int | None = Field(default=None, ge=0, le=10000)


class UnsupportedQuestionError(ValueError):
    """Raised when the local router abstains from selecting an approved tool."""


class LocalIntentModel:
    """Apply deterministic policy around one injected local model adapter."""

    def __init__(
        self,
        confidence_threshold: float = 0.38,
        adapter: IntentModelAdapter | None = None,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.adapter = adapter or TfidfLogisticIntentAdapter()
        self.version = self.adapter.model_version

    def provenance(self) -> dict:
        """Describe the active inference boundary without exposing model internals."""

        artifact_sha256 = self.adapter.artifact_sha256
        return {
            "classification_inference": {
                "implemented": True,
                "scope": "intent classification only",
                "location": self.adapter.inference_location,
                "network_required": self.adapter.network_required,
            },
            "generative_inference": {
                "implemented": False,
                "answer_mode": "deterministic template",
            },
            "adapter": self.adapter.adapter_name,
            "model": self.adapter.model_name,
            "model_version": self.adapter.model_version,
            "approved_labels": [
                "compare_delivery_periods",
                "delivery_exceptions",
                "delivery_summary",
                "unsupported",
            ],
            "confidence_threshold": self.confidence_threshold,
            "artifact": {
                "mode": "verified persisted artifact"
                if artifact_sha256
                else "in-memory development fit",
                "sha256": artifact_sha256,
            },
        }

    def predict(self, question: str) -> dict:
        prediction = self.adapter.predict(question)
        if prediction.label not in {
            "delivery_summary",
            "compare_delivery_periods",
            "delivery_exceptions",
            "unsupported",
        }:
            raise ValueError(f"Model adapter returned unapproved label: {prediction.label}")
        if not 0 <= prediction.confidence <= 1 or not math.isfinite(prediction.confidence):
            raise ValueError("Model adapter returned invalid confidence")
        if not 0 <= prediction.confidence_margin <= 1 or not math.isfinite(
            prediction.confidence_margin
        ):
            raise ValueError("Model adapter returned invalid confidence margin")
        guardrail = next(
            (name for name, pattern in BLOCKED_PATTERNS.items() if pattern.search(question)),
            None,
        )
        if (
            guardrail is None
            and DOMAIN_PATTERN.search(question) is None
            and COMPARISON_CONTEXT_PATTERN.search(question) is None
        ):
            guardrail = "out_of_domain"
        accepted = (
            guardrail is None
            and prediction.label != "unsupported"
            and prediction.confidence >= self.confidence_threshold
        )
        return {
            "label": prediction.label,
            "confidence": round(prediction.confidence, 6),
            "confidence_margin": round(prediction.confidence_margin, 6),
            "accepted": accepted,
            "threshold": self.confidence_threshold,
            "guardrail": guardrail,
            "model": self.adapter.model_name,
            "model_version": self.adapter.model_version,
            "model_adapter": self.adapter.adapter_name,
            "inference_location": self.adapter.inference_location,
            "network_required": self.adapter.network_required,
            "model_artifact_sha256": self.adapter.artifact_sha256,
        }

    def route(self, request: QuestionRequest) -> tuple[ToolRequest | None, dict]:
        """Return one prediction and its validated tool request, or abstain."""

        routing = self.predict(request.question)
        if not routing["accepted"]:
            return None, routing
        payload = request.model_dump(exclude={"question"})
        payload["name"] = routing["label"]
        return ToolRequest.model_validate(payload), routing

    def plan(self, request: QuestionRequest) -> tuple[ToolRequest, dict]:
        """Return an approved plan or preserve the existing exception contract."""

        tool_request, routing = self.route(request)
        if tool_request is None:
            raise UnsupportedQuestionError(
                "Question was not confidently routed to an approved read-only tool"
            )
        return tool_request, routing
