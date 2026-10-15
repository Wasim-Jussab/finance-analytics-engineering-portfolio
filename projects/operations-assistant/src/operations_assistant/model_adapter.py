"""Swappable local inference boundary for governed intent routing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

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


@dataclass(frozen=True)
class AdapterPrediction:
    """Model-only result before deterministic policy and tool validation."""

    label: str
    confidence: float
    confidence_margin: float


@runtime_checkable
class IntentModelAdapter(Protocol):
    """Minimum local inference contract accepted by the governed router."""

    adapter_name: str
    model_name: str
    model_version: str
    inference_location: str
    network_required: bool
    artifact_sha256: str | None

    def predict(self, question: str) -> AdapterPrediction:
        """Return one model prediction without selecting or executing a tool."""


class TfidfLogisticIntentAdapter:
    """Fit and execute the current classifier entirely in local memory."""

    adapter_name = "local-intent-adapter-v1"
    model_name = "local-tfidf-logistic-regression"
    inference_location = "local-process"
    network_required = False

    @classmethod
    def specification(cls) -> dict:
        """Return the complete versioned training and estimator specification."""

        return {
            "training_examples": TRAINING_EXAMPLES,
            "tfidf": {"ngram_range": [1, 2], "sublinear_tf": True},
            "logistic_regression": {"C": 4, "max_iter": 1000, "random_state": 42},
            "sklearn_version": sklearn.__version__,
        }

    def __init__(
        self,
        pipeline: Pipeline | None = None,
        artifact_sha256: str | None = None,
    ) -> None:
        specification = self.specification()
        self.model_version = hashlib.sha256(
            json.dumps(specification, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:12]
        if pipeline is None:
            pipeline = Pipeline(
                [
                    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
                    (
                        "classifier",
                        LogisticRegression(C=4, max_iter=1000, random_state=42),
                    ),
                ]
            )
            texts, labels = zip(*TRAINING_EXAMPLES, strict=True)
            pipeline.fit(texts, labels)
        self.pipeline = pipeline
        self.artifact_sha256 = artifact_sha256

    def predict(self, question: str) -> AdapterPrediction:
        probabilities = self.pipeline.predict_proba([question])[0]
        classes = self.pipeline.classes_
        best_index = int(probabilities.argmax())
        ordered = sorted((float(value) for value in probabilities), reverse=True)
        return AdapterPrediction(
            label=str(classes[best_index]),
            confidence=float(probabilities[best_index]),
            confidence_margin=ordered[0] - ordered[1],
        )
