"""Execute fixed routing regressions and audit reference-training overlap."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from operations_assistant.intent import LocalIntentModel
from operations_assistant.model_adapter import TRAINING_EXAMPLES
from operations_assistant.model_artifact import load_model_artifact

EVALUATION_CASES = (
    ("Give me a snapshot of delivery results", "delivery_summary"),
    ("How many orders missed their promise?", "delivery_summary"),
    ("Show on-time performance for London", "delivery_summary"),
    ("What are the delivery counts for this date range?", "delivery_summary"),
    ("Report open overdue shipments", "delivery_summary"),
    ("How does the current week compare with the prior week?", "compare_delivery_periods"),
    ("Show changes in delivery outcomes", "compare_delivery_periods"),
    ("Did the completion rate improve against baseline?", "compare_delivery_periods"),
    ("Which region lost the most on-time deliveries?", "compare_delivery_periods"),
    ("Contrast late shipment counts across both periods", "compare_delivery_periods"),
    ("Which individual shipments are currently overdue or late?", "delivery_exceptions"),
    ("Show me the individual missed-promise rows", "delivery_exceptions"),
    ("List the five worst delivery exceptions", "delivery_exceptions"),
    ("Drop the raw table", "unsupported"),
    ("Explain the root cause of every delay", "unsupported"),
    ("Email the worst performing depot", "unsupported"),
    ("Forecast delivery performance next quarter", "unsupported"),
    ("Create a song about parcels", "unsupported"),
)

OVERLAP_NORMALIZATION = 'lowercase ASCII alphanumeric tokens; collapsed whitespace'


def normalize_question(question: str) -> str:
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', question.lower()).split())


def run_intent_evaluation(model: LocalIntentModel | None = None) -> dict:
    model = model or LocalIntentModel()
    results = []
    training = {normalize_question(question) for question, _label in TRAINING_EXAMPLES}
    for question, expected in EVALUATION_CASES:
        prediction = model.predict(question)
        observed = prediction["label"] if prediction["accepted"] else "unsupported"
        results.append(
            {
                "question": question,
                "expected": expected,
                "observed": observed,
                "confidence": prediction["confidence"],
                "passed": observed == expected,
                "overlaps_reference_training": normalize_question(question) in training,
            }
        )
    passed = sum(result["passed"] for result in results)
    overlapping = sum(result['overlaps_reference_training'] for result in results)
    return {
        "mode": "executed local intent-model inference; no generative model",
        "model": "local-tfidf-logistic-regression",
        "model_version": model.version,
        "model_artifact_sha256": model.adapter.artifact_sha256,
        "cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "reference_training_overlap": {
            "normalization": OVERLAP_NORMALIZATION,
            "overlapping_cases": overlapping,
            "non_overlapping_cases": len(results) - overlapping,
            "independent_holdout_claim_supported": False,
            "limitation": (
                "Fixed previously used regression cases, not an independent holdout. "
                "Non-overlap does not establish semantic novelty or absence of tuning. "
                "Overlap is relative to this repository's reference training examples."
            ),
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/intent-evaluation.json"))
    parser.add_argument("--model-artifact", type=Path)
    arguments = parser.parse_args()
    model = (
        LocalIntentModel(adapter=load_model_artifact(arguments.model_artifact))
        if arguments.model_artifact
        else None
    )
    result = run_intent_evaluation(model)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = arguments.output.with_suffix(f"{arguments.output.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(arguments.output)
    print(f"Intent routing evaluation: {result['passed']}/{result['cases']} passed")
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
