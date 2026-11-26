"""Apply an explicit release policy to executed local routing evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from operations_assistant.intent_evaluation import (
    OVERLAP_NORMALIZATION,
    normalize_question,
    summarize_decisions,
)
from operations_assistant.model_adapter import TRAINING_EXAMPLES

RELEASE_EVALUATOR_VERSION = "1.3.0"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label.capitalize()} must contain an object")
    return value


def load_release_policy(path: Path) -> dict:
    policy = _load_json(path, "routing release policy")
    required = {
        "require_all_held_out_cases_pass",
        "require_all_adversarial_cases_pass",
        "maximum_unsafe_acceptances",
        "required_risk_slices",
    }
    if set(policy) != required:
        raise ValueError(f"Routing release policy must contain exactly: {sorted(required)}")
    if not isinstance(policy["require_all_held_out_cases_pass"], bool):
        raise ValueError("require_all_held_out_cases_pass must be true or false")
    if not isinstance(policy["require_all_adversarial_cases_pass"], bool):
        raise ValueError("require_all_adversarial_cases_pass must be true or false")
    maximum = policy["maximum_unsafe_acceptances"]
    if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum < 0:
        raise ValueError("maximum_unsafe_acceptances must be a non-negative integer")
    slices = policy["required_risk_slices"]
    if (
        not isinstance(slices, list)
        or not slices
        or any(not isinstance(name, str) or not name for name in slices)
        or len(slices) != len(set(slices))
    ):
        raise ValueError("required_risk_slices must contain unique non-empty names")
    return policy


def _validate_evaluation(report: dict, label: str) -> None:
    results = report.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError(f"{label} evaluation must contain results")
    for result in results:
        if not isinstance(result, dict):
            raise ValueError(f"{label} evaluation contains an invalid result")
        expected = result.get("expected")
        observed = result.get("observed")
        if not isinstance(expected, str) or not isinstance(observed, str):
            raise ValueError(f"{label} evaluation result must contain labels")
        if result.get("passed") != (observed == expected):
            raise ValueError(f"{label} evaluation result has inconsistent pass evidence")
    passed = sum(result["passed"] for result in results)
    if (
        report.get("cases") != len(results)
        or report.get("passed") != passed
        or report.get("failed") != len(results) - passed
    ):
        raise ValueError(f"{label} evaluation totals do not reconcile")
    if not isinstance(report.get("model_version"), str) or not report["model_version"]:
        raise ValueError(f"{label} evaluation must identify the model version")


def _validate_reference_overlap(report: dict) -> None:
    audit = report.get("reference_training_overlap")
    if not isinstance(audit, dict):
        raise ValueError("Fixed-routing evaluation must contain a reference-training overlap audit")
    if audit.get("normalization") != OVERLAP_NORMALIZATION:
        raise ValueError("Reference-training overlap normalization does not match")
    if audit.get("independent_holdout_claim_supported") is not False:
        raise ValueError("Reference-training overlap must not claim an independent holdout")
    training = {normalize_question(question) for question, _label in TRAINING_EXAMPLES}
    overlapping = 0
    for row in report["results"]:
        question, flag = row.get("question"), row.get("overlaps_reference_training")
        if not isinstance(question, str) or not question.strip() or not isinstance(flag, bool):
            raise ValueError("Reference-training overlap case evidence is missing or invalid")
        actual = normalize_question(question) in training
        if flag is not actual:
            raise ValueError("Reference-training overlap case flag does not match the reference")
        overlapping += actual
    expected = {
        "overlapping_cases": overlapping,
        "non_overlapping_cases": len(report["results"]) - overlapping,
    }
    for key, count in expected.items():
        if type(audit.get(key)) is not int or audit[key] != count:
            raise ValueError("Reference-training overlap totals do not reconcile")


def _validate_decision_diagnostics(report: dict) -> None:
    diagnostics = report.get("decision_diagnostics")
    if not isinstance(diagnostics, dict):
        raise ValueError("Decision diagnostics are required")
    approved = {
        "delivery_summary",
        "compare_delivery_periods",
        "delivery_exceptions",
        "unsupported",
    }
    for row in report["results"]:
        label, accepted, guardrail = (
            row.get("model_label"),
            row.get("accepted"),
            row.get("guardrail"),
        )
        if (
            not isinstance(label, str)
            or label not in approved
            or not isinstance(accepted, bool)
            or "guardrail" not in row
            or (guardrail is not None and (not isinstance(guardrail, str) or not guardrail))
        ):
            raise ValueError("Decision diagnostic case evidence is invalid")
        if accepted and (guardrail is not None or label == "unsupported"):
            raise ValueError("Decision diagnostic acceptance contradicts case evidence")
        observed = label if accepted else "unsupported"
        reason = (
            "guardrail"
            if guardrail
            else "model_unsupported"
            if label == "unsupported"
            else "accepted"
            if accepted
            else "below_threshold"
        )
        if row["observed"] != observed or row.get("decision_reason") != reason:
            raise ValueError("Decision diagnostic outcome or reason does not reconcile")
    expected = summarize_decisions(report["results"])
    for field in ("raw_label_matches", "governed_label_matches"):
        value = diagnostics.get(field)
        if type(value) is not int or value != expected[field]:
            raise ValueError("Decision diagnostic match counts do not reconcile")
    counts = diagnostics.get("decision_counts")
    if (
        not isinstance(counts, dict)
        or set(counts) != set(expected["decision_counts"])
        or any(type(v) is not int for v in counts.values())
        or counts != expected["decision_counts"]
    ):
        raise ValueError("Decision diagnostic reason counts do not reconcile")


def evaluate_release(held_out: dict, adversarial: dict, policy: dict) -> dict:
    """Return a release decision derived from reconciled evaluation case evidence."""

    _validate_evaluation(held_out, "held-out")
    _validate_evaluation(adversarial, "adversarial")
    _validate_reference_overlap(held_out)
    _validate_decision_diagnostics(held_out)
    if held_out.get("model") != adversarial.get("model"):
        raise ValueError("Evaluation reports identify different model types")
    if held_out["model_version"] != adversarial["model_version"]:
        raise ValueError("Evaluation reports identify different model versions")
    if held_out.get("model_artifact_sha256") != adversarial.get("model_artifact_sha256"):
        raise ValueError("Evaluation reports identify different model artifacts")

    adversarial_results = adversarial["results"]
    unsafe_acceptances = sum(
        result["expected"] == "unsupported" and result["observed"] != "unsupported"
        for result in adversarial_results
    )
    observed_slices = {
        result.get("risk_slice")
        for result in adversarial_results
        if isinstance(result.get("risk_slice"), str)
    }
    missing_slices = sorted(set(policy["required_risk_slices"]) - observed_slices)
    breaches = []
    if policy["require_all_held_out_cases_pass"] and held_out["failed"]:
        breaches.append(
            {
                "check": "require_all_held_out_cases_pass",
                "observed": held_out["failed"],
                "threshold": 0,
            }
        )
    if policy["require_all_adversarial_cases_pass"] and adversarial["failed"]:
        breaches.append(
            {
                "check": "require_all_adversarial_cases_pass",
                "observed": adversarial["failed"],
                "threshold": 0,
            }
        )
    if unsafe_acceptances > policy["maximum_unsafe_acceptances"]:
        breaches.append(
            {
                "check": "maximum_unsafe_acceptances",
                "observed": unsafe_acceptances,
                "threshold": policy["maximum_unsafe_acceptances"],
            }
        )
    if missing_slices:
        breaches.append(
            {
                "check": "required_risk_slices",
                "observed": missing_slices,
                "threshold": policy["required_risk_slices"],
            }
        )
    return {
        "status": "approved" if not breaches else "blocked",
        "model": held_out["model"],
        "model_version": held_out["model_version"],
        "model_artifact_sha256": held_out.get("model_artifact_sha256"),
        "held_out_cases": held_out["cases"],
        "held_out_passed": held_out["passed"],
        "evaluation_scope": {
            "suite": "fixed routing regressions; legacy held_out keys retained",
            "reference_training_overlap": held_out.get("reference_training_overlap"),
            "independent_holdout_claim_supported": False,
        },
        "adversarial_cases": adversarial["cases"],
        "adversarial_passed": adversarial["passed"],
        "unsafe_acceptances": unsafe_acceptances,
        "observed_risk_slices": sorted(observed_slices),
        "breaches": breaches,
        "criteria": policy,
        "interpretation": (
            "Release gate over named local routing fixtures; not a production accuracy estimate."
        ),
    }


def build_release_decision(held_out_path: Path, adversarial_path: Path, policy_path: Path) -> dict:
    held_out = _load_json(held_out_path, "held-out evaluation")
    adversarial = _load_json(adversarial_path, "adversarial evaluation")
    policy = load_release_policy(policy_path)
    result = evaluate_release(held_out, adversarial, policy)
    evidence = {
        "evaluator_version": RELEASE_EVALUATOR_VERSION,
        "held_out_evaluation_sha256": _sha256(held_out_path),
        "adversarial_evaluation_sha256": _sha256(adversarial_path),
        "policy_sha256": _sha256(policy_path),
        "status": result["status"],
        "breaches": result["breaches"],
    }
    release_id = hashlib.sha256(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**result, "release_evidence": {"release_id": release_id, **evidence}}


def write_release_decision(
    held_out_path: Path,
    adversarial_path: Path,
    policy_path: Path,
    output_path: Path,
) -> dict:
    result = build_release_decision(held_out_path, adversarial_path, policy_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--held-out", type=Path, default=Path("reports/intent-evaluation.json"))
    parser.add_argument(
        "--adversarial", type=Path, default=Path("reports/adversarial-evaluation.json")
    )
    parser.add_argument("--policy", type=Path, default=Path("config/routing-release-policy.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/routing-release.json"))
    arguments = parser.parse_args()
    result = write_release_decision(
        arguments.held_out, arguments.adversarial, arguments.policy, arguments.output
    )
    print(
        f"Routing release: {result['status']}; "
        f"fixed routing cases {result['held_out_passed']}/{result['held_out_cases']}; "
        f"adversarial {result['adversarial_passed']}/{result['adversarial_cases']}"
    )
    return 0 if result["status"] == "approved" else 1


if __name__ == "__main__":
    raise SystemExit(main())
