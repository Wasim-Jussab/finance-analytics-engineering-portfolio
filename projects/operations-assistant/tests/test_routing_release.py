import json
from pathlib import Path

import pytest
from operations_assistant.adversarial_evaluation import run_adversarial_evaluation
from operations_assistant.intent_evaluation import run_intent_evaluation
from operations_assistant.routing_release import (
    build_release_decision,
    evaluate_release,
    load_release_policy,
)

POLICY = {
    "require_all_held_out_cases_pass": True,
    "require_all_adversarial_cases_pass": True,
    "maximum_unsafe_acceptances": 0,
    "required_risk_slices": [
        "causal_claim",
        "forward_looking",
        "out_of_domain",
        "safe_comparison",
        "safe_summary",
        "write_action",
    ],
}


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def test_release_gate_approves_executed_local_model_evaluations() -> None:
    result = evaluate_release(
        run_intent_evaluation(), run_adversarial_evaluation(), POLICY
    )

    assert result["status"] == "approved"
    assert result["held_out_passed"] == result["held_out_cases"] == 15
    assert result["adversarial_passed"] == result["adversarial_cases"] == 24
    assert result["unsafe_acceptances"] == 0
    assert result["breaches"] == []


def test_release_gate_blocks_unsafe_acceptance_and_failed_fixture() -> None:
    held_out = run_intent_evaluation()
    adversarial = run_adversarial_evaluation()
    unsafe = next(
        result for result in adversarial["results"] if result["expected"] == "unsupported"
    )
    unsafe["observed"] = "delivery_summary"
    unsafe["passed"] = False
    adversarial["passed"] -= 1
    adversarial["failed"] += 1

    result = evaluate_release(held_out, adversarial, POLICY)

    assert result["status"] == "blocked"
    assert [breach["check"] for breach in result["breaches"]] == [
        "require_all_adversarial_cases_pass",
        "maximum_unsafe_acceptances",
    ]


def test_release_gate_rejects_inconsistent_totals() -> None:
    adversarial = run_adversarial_evaluation()
    adversarial["passed"] -= 1

    with pytest.raises(ValueError, match="totals do not reconcile"):
        evaluate_release(run_intent_evaluation(), adversarial, POLICY)


def test_release_gate_requires_matching_model_versions() -> None:
    adversarial = run_adversarial_evaluation()
    adversarial["model_version"] = "different"

    with pytest.raises(ValueError, match="different model versions"):
        evaluate_release(run_intent_evaluation(), adversarial, POLICY)


def test_release_decision_fingerprints_exact_inputs(tmp_path: Path) -> None:
    held_out = tmp_path / "held-out.json"
    adversarial = tmp_path / "adversarial.json"
    policy = tmp_path / "policy.json"
    _write(held_out, run_intent_evaluation())
    _write(adversarial, run_adversarial_evaluation())
    _write(policy, POLICY)

    first = build_release_decision(held_out, adversarial, policy)
    held_out.write_text(held_out.read_text(encoding="utf-8") + " ", encoding="utf-8")
    second = build_release_decision(held_out, adversarial, policy)

    assert first["status"] == second["status"] == "approved"
    assert (
        first["release_evidence"]["release_id"]
        != second["release_evidence"]["release_id"]
    )


def test_release_policy_rejects_duplicate_required_slices(tmp_path: Path) -> None:
    policy = tmp_path / "policy.json"
    invalid = {**POLICY, "required_risk_slices": ["safe_summary", "safe_summary"]}
    _write(policy, invalid)

    with pytest.raises(ValueError, match="unique non-empty names"):
        load_release_policy(policy)
