from copy import deepcopy
from pathlib import Path

import pytest
from operations_assistant.adversarial_evaluation import run_adversarial_evaluation
from operations_assistant.intent_evaluation import run_intent_evaluation
from operations_assistant.routing_release import evaluate_release, load_release_policy


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_summary",
        "raw_count",
        "governed_count",
        "reason_count",
        "float_count",
        "missing_label",
        "accepted_type",
        "accepted_guardrail",
        "reason",
        "unknown_counter",
    ],
)
def test_release_refuses_inconsistent_decision_diagnostics(mutation):
    report = deepcopy(run_intent_evaluation())
    diagnostics = report["decision_diagnostics"]
    if mutation == "missing_summary":
        report.pop("decision_diagnostics")
    elif mutation == "raw_count":
        diagnostics["raw_label_matches"] += 1
    elif mutation == "governed_count":
        diagnostics["governed_label_matches"] -= 1
    elif mutation == "reason_count":
        diagnostics["decision_counts"]["accepted"] += 1
    elif mutation == "float_count":
        diagnostics["raw_label_matches"] = float(diagnostics["raw_label_matches"])
    elif mutation == "missing_label":
        report["results"][0].pop("model_label")
    elif mutation == "accepted_type":
        report["results"][0]["accepted"] = 1
    elif mutation == "accepted_guardrail":
        row = next(r for r in report["results"] if r["guardrail"])
        row["accepted"] = True
    elif mutation == "reason":
        report["results"][0]["decision_reason"] = "made_up_reason"
    else:
        diagnostics["decision_counts"]["unknown_reason"] = 0
    assert report["passed"] == report["cases"] == 18
    with pytest.raises(ValueError, match="[Dd]iagnostic"):
        evaluate_release(
            report,
            run_adversarial_evaluation(),
            load_release_policy(Path("config/routing-release-policy.json")),
        )
