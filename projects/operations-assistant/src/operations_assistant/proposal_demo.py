"""Run one approved comparison end to end on a fresh synthetic snapshot."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from operations_assistant.answers import render_answer
from operations_assistant.decision_trace import build_decision_trace, verify_answer_binding
from operations_assistant.generate import build_snapshot
from operations_assistant.intent import LocalIntentModel, QuestionRequest
from operations_assistant.model_artifact import load_model_artifact
from operations_assistant.proposal_adapter import ClassifierProposalAdapter, plan_with_adapter
from operations_assistant.runtime_readiness import build_runtime_readiness
from operations_assistant.tools import execute_tool


def run_demo(model_artifact: Path, routing_release: Path, question_release: Path) -> dict:
    readiness = build_runtime_readiness(model_artifact, routing_release, question_release)
    if readiness["status"] != "ready":
        checks = ", ".join(item["check"] for item in readiness["breaches"])
        raise ValueError(f"Runtime readiness blocked: {checks}")

    model = load_model_artifact(model_artifact)
    if model.artifact_sha256 != readiness["model_artifact_sha256"]:
        raise ValueError("Loaded classifier differs from the approved artifact")

    router = LocalIntentModel(adapter=model)
    scope = QuestionRequest(
        question="How does the current week compare with the prior week?",
        start="2026-09-21",
        end="2026-09-28",
        baseline_start="2026-09-14",
        baseline_end="2026-09-21",
    )
    request, routing = plan_with_adapter(scope, ClassifierProposalAdapter(router), router)
    if request.name != "compare_delivery_periods":
        raise ValueError("The demo must select the approved period comparison")

    with TemporaryDirectory(prefix="operations-proposal-demo-") as directory:
        database = Path(directory) / "synthetic.duckdb"
        build_snapshot(database)
        answer = render_answer(execute_tool(database, request))

    trace = build_decision_trace(scope, routing, "answered", request, answer)
    verify_answer_binding(trace, answer)
    return {
        "demo": "synthetic weekly delivery comparison",
        "runtime_readiness": readiness,
        "routing": routing,
        "decision_trace": trace,
        "generative_inference": False,
        **answer,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-artifact", type=Path, default=Path("artifacts/local-intent-model"))
    parser.add_argument(
        "--routing-release", type=Path, default=Path("reports/routing-release.json")
    )
    parser.add_argument(
        "--question-release", type=Path, default=Path("reports/question-release.json")
    )
    args = parser.parse_args()
    try:
        result = run_demo(args.model_artifact, args.routing_release, args.question_release)
    except ValueError as error:
        parser.exit(1, f"Proposal demo blocked: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
