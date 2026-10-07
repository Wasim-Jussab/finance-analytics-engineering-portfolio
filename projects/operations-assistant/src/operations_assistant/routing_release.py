"""Apply an explicit release policy to executed local routing evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

RELEASE_EVALUATOR_VERSION = "1.0.0"


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


def evaluate_release(held_out: dict, adversarial: dict, policy: dict) -> dict:
    """Return a release decision derived from reconciled evaluation case evidence."""

    _validate_evaluation(held_out, "held-out")
    _validate_evaluation(adversarial, "adversarial")
    if held_out.get("model") != adversarial.get("model"):
        raise ValueError("Evaluation reports identify different model types")
    if held_out["model_version"] != adversarial["model_version"]:
        raise ValueError("Evaluation reports identify different model versions")

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
        "held_out_cases": held_out["cases"],
        "held_out_passed": held_out["passed"],
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


def build_release_decision(
    held_out_path: Path, adversarial_path: Path, policy_path: Path
) -> dict:
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
    parser.add_argument(
        "--held-out", type=Path, default=Path("reports/intent-evaluation.json")
    )
    parser.add_argument(
        "--adversarial", type=Path, default=Path("reports/adversarial-evaluation.json")
    )
    parser.add_argument(
        "--policy", type=Path, default=Path("config/routing-release-policy.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("reports/routing-release.json")
    )
    arguments = parser.parse_args()
    result = write_release_decision(
        arguments.held_out, arguments.adversarial, arguments.policy, arguments.output
    )
    print(
        f"Routing release: {result['status']}; "
        f"held-out {result['held_out_passed']}/{result['held_out_cases']}; "
        f"adversarial {result['adversarial_passed']}/{result['adversarial_cases']}"
    )
    return 0 if result["status"] == "approved" else 1


if __name__ == "__main__":
    raise SystemExit(main())
