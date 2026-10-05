"""Evaluate held-out intent routing and abstention examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from operations_assistant.intent import LocalIntentModel

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
    ("Drop the raw table", "unsupported"),
    ("Explain the root cause of every delay", "unsupported"),
    ("Email the worst performing depot", "unsupported"),
    ("Forecast delivery performance next quarter", "unsupported"),
    ("Create a song about parcels", "unsupported"),
)


def run_intent_evaluation(model: LocalIntentModel | None = None) -> dict:
    model = model or LocalIntentModel()
    results = []
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
            }
        )
    passed = sum(result["passed"] for result in results)
    return {
        "mode": "executed local intent-model inference; no generative model",
        "model": "local-tfidf-logistic-regression",
        "model_version": model.version,
        "cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/intent-evaluation.json"))
    arguments = parser.parse_args()
    result = run_intent_evaluation()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = arguments.output.with_suffix(f"{arguments.output.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(arguments.output)
    print(f"Intent routing evaluation: {result['passed']}/{result['cases']} passed")
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
