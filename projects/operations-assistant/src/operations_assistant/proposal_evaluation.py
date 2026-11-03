"""Execute proposal planning against the existing routing fixtures, not a new holdout."""

import argparse
import json
from pathlib import Path

from operations_assistant.intent import LocalIntentModel, QuestionRequest, UnsupportedQuestionError
from operations_assistant.intent_evaluation import EVALUATION_CASES
from operations_assistant.model_artifact import load_model_artifact
from operations_assistant.proposal_adapter import ClassifierProposalAdapter, plan_with_adapter


def evaluate(router: LocalIntentModel, adapter=None) -> dict:
    adapter = adapter or ClassifierProposalAdapter(router)
    results = []
    for index, (question, expected) in enumerate(EVALUATION_CASES):
        arguments = {"start": "2026-09-21", "end": "2026-09-28"}
        if expected == "compare_delivery_periods":
            arguments.update(baseline_start="2026-09-14", baseline_end="2026-09-21")
        scope = QuestionRequest(question=question, **arguments)
        observed, error_type = None, None
        try:
            request, _ = plan_with_adapter(scope, adapter, router)
            observed = request.name
        except UnsupportedQuestionError:
            observed = "unsupported"
        except ValueError as error:
            error_type = type(error).__name__
        results.append(
            {
                "case_id": index + 1,
                "expected": expected,
                "observed": observed,
                "error_type": error_type,
                "passed": observed == expected,
            }
        )
    passed = sum(row["passed"] for row in results)
    return {
        "mode": "executed proposal planning; existing routing fixtures reused",
        "adapter": adapter.adapter_name,
        "model_version": router.version,
        "model_artifact_sha256": router.adapter.artifact_sha256,
        "generative_inference": False,
        "tools_executed": False,
        "cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("reports/proposal-evaluation.json"))
    args = parser.parse_args()
    router = LocalIntentModel(adapter=load_model_artifact(args.model_artifact))
    result = evaluate(router)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n")
    temporary.replace(args.output)
    print(f"Proposal planning evaluation: {result['passed']}/{result['cases']} passed")
    raise SystemExit(0 if result["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
