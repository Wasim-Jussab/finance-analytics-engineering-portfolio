"""A small local model that routes questions to approved read-only tools."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from operations_assistant.tools import ToolRequest

TRAINING_EXAMPLES = (
    ("summarise delivery performance", "delivery_summary"),
    ("show the on time completion rate", "delivery_summary"),
    ("how many shipments were late", "delivery_summary"),
    ("give me the delivery totals", "delivery_summary"),
    ("what is the overdue open count", "delivery_summary"),
    ("report delivery performance for the selected period", "delivery_summary"),
    ("show delivery outcomes by region", "delivery_summary"),
    ("what percentage arrived on time", "delivery_summary"),
    ("how is the north performing", "delivery_summary"),
    ("count cancelled shipments", "delivery_summary"),
    ("report shipments that remain overdue and open", "delivery_summary"),
    ("summarise shipments due for the selected period", "delivery_summary"),
    ("give me the due delivery summary", "delivery_summary"),
    ("compare delivery performance between periods", "compare_delivery_periods"),
    ("how did this week change from last week", "compare_delivery_periods"),
    ("show the movement in late deliveries", "compare_delivery_periods"),
    ("was the on time rate better than the baseline", "compare_delivery_periods"),
    ("which region declined most versus last week", "compare_delivery_periods"),
    ("compare current and previous delivery outcomes", "compare_delivery_periods"),
    ("what changed in overdue shipments", "compare_delivery_periods"),
    ("give me the week on week difference", "compare_delivery_periods"),
    ("show percentage point change", "compare_delivery_periods"),
    ("contrast these two reporting periods", "compare_delivery_periods"),
    ("did completion improve compared with the baseline", "compare_delivery_periods"),
    ("delete the shipments table", "unsupported"),
    ("update every delivery status", "unsupported"),
    ("write arbitrary sql", "unsupported"),
    ("why did the courier fail", "unsupported"),
    ("predict next month's delivery rate", "unsupported"),
    ("send a message to the depot", "unsupported"),
    ("write me a poem", "unsupported"),
    ("change the promised date", "unsupported"),
    ("tell me who is to blame", "unsupported"),
    ("forecast future demand", "unsupported"),
    ("forecast delivery performance for a future quarter", "unsupported"),
)

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
    baseline_start: date | None = None
    baseline_end: date | None = None


class UnsupportedQuestionError(ValueError):
    """Raised when the local router abstains from selecting an approved tool."""


class LocalIntentModel:
    """Fit a reproducible TF-IDF logistic classifier entirely in process."""

    def __init__(self, confidence_threshold: float = 0.38) -> None:
        self.confidence_threshold = confidence_threshold
        self.pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
                (
                    "classifier",
                    LogisticRegression(C=4, max_iter=1000, random_state=42),
                ),
            ]
        )
        texts, labels = zip(*TRAINING_EXAMPLES, strict=True)
        self.pipeline.fit(texts, labels)
        self.version = hashlib.sha256(
            json.dumps(TRAINING_EXAMPLES, separators=(",", ":")).encode()
        ).hexdigest()[:12]

    def predict(self, question: str) -> dict:
        probabilities = self.pipeline.predict_proba([question])[0]
        classes = self.pipeline.classes_
        best_index = int(probabilities.argmax())
        label = str(classes[best_index])
        confidence = float(probabilities[best_index])
        ordered = sorted((float(value) for value in probabilities), reverse=True)
        confidence_margin = ordered[0] - ordered[1]
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
            and label != "unsupported"
            and confidence >= self.confidence_threshold
        )
        return {
            "label": label,
            "confidence": round(confidence, 6),
            "confidence_margin": round(confidence_margin, 6),
            "accepted": accepted,
            "threshold": self.confidence_threshold,
            "guardrail": guardrail,
            "model": "local-tfidf-logistic-regression",
            "model_version": self.version,
        }

    def plan(self, request: QuestionRequest) -> tuple[ToolRequest, dict]:
        routing = self.predict(request.question)
        if not routing["accepted"]:
            raise UnsupportedQuestionError(
                "Question was not confidently routed to an approved read-only tool"
            )
        payload = request.model_dump(exclude={"question"})
        payload["name"] = routing["label"]
        return ToolRequest.model_validate(payload), routing
