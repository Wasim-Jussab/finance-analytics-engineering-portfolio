"""Apply a versioned release policy to the executed question-path evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

RELEASE_EVALUATOR_VERSION = "1.0.0"
POLICY_FIELDS = {
    "require_all_cases_pass",
    "expected_answered_cases",
    "expected_blocked_cases",
    "maximum_blocked_tool_executions",
    "require_database_unchanged",
    "require_unique_decision_traces",
}


def _load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label.capitalize()} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_question_release_policy(path: Path) -> dict:
    policy = _load_object(path, "question release policy")
    if set(policy) != POLICY_FIELDS:
        raise ValueError(
            f"Question release policy must contain exactly: {sorted(POLICY_FIELDS)}"
        )
    for field in (
        "require_all_cases_pass",
        "require_database_unchanged",
        "require_unique_decision_traces",
    ):
        if not isinstance(policy[field], bool):
            raise ValueError(f"{field} must be true or false")
    for field in (
        "expected_answered_cases",
        "expected_blocked_cases",
        "maximum_blocked_tool_executions",
    ):
        value = policy[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{field} must be a non-negative integer")
    return policy


def _validate_evaluation(report: dict) -> list[dict]:
    results = report.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("Question evaluation must contain results")
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("Question evaluation contains an invalid result")
        failures = result.get("failures")
        if not isinstance(failures, list):
            raise ValueError("Question evaluation result must contain failures")
        expected = result.get("expected_outcome")
        observed = result.get("observed_outcome")
        if expected not in {"answered", "blocked"} or observed not in {
            "answered",
            "blocked",
        }:
            raise ValueError("Question evaluation result has an invalid outcome")
        if result.get("passed") != (expected == observed and not failures):
            raise ValueError("Question evaluation result has inconsistent pass evidence")
        decision_id = result.get("decision_id")
        if not isinstance(decision_id, str) or not decision_id:
            raise ValueError("Question evaluation result must contain a decision ID")
        if expected == "answered" and (
            not isinstance(result.get("tool"), str)
            or not isinstance(result.get("evidence_id"), str)
        ):
            raise ValueError("Answered result must identify its tool and evidence")
        if expected == "blocked" and result.get("evidence_id") is not None:
            raise ValueError("Blocked result must not contain executed-tool evidence")

    passed = sum(result["passed"] for result in results)
    if (
        report.get("cases") != len(results)
        or report.get("passed") != passed
        or report.get("failed") != len(results) - passed
    ):
        raise ValueError("Question evaluation totals do not reconcile")
    if report.get("answered_cases") != sum(
        result["expected_outcome"] == "answered" for result in results
    ):
        raise ValueError("Question evaluation answered-case total does not reconcile")
    if report.get("blocked_cases") != sum(
        result["expected_outcome"] == "blocked" for result in results
    ):
        raise ValueError("Question evaluation blocked-case total does not reconcile")
    if report.get("tool_executions") != sum(
        result["observed_outcome"] == "answered" for result in results
    ):
        raise ValueError("Question evaluation tool-execution total does not reconcile")
    return results


def evaluate_question_release(report: dict, policy: dict) -> dict:
    """Return a release decision over reconciled end-to-end question evidence."""

    results = _validate_evaluation(report)
    answered = report["answered_cases"]
    blocked = report["blocked_cases"]
    blocked_tool_executions = sum(
        result["expected_outcome"] == "blocked" and result.get("tool") is not None
        for result in results
    )
    decision_ids = [result["decision_id"] for result in results]
    unique_decision_traces = len(set(decision_ids))
    breaches = []
    checks = (
        ("require_all_cases_pass", report["failed"], 0),
        ("expected_answered_cases", answered, policy["expected_answered_cases"]),
        ("expected_blocked_cases", blocked, policy["expected_blocked_cases"]),
        (
            "maximum_blocked_tool_executions",
            blocked_tool_executions,
            policy["maximum_blocked_tool_executions"],
        ),
    )
    if policy["require_all_cases_pass"] and report["failed"]:
        breaches.append({"check": checks[0][0], "observed": checks[0][1], "threshold": 0})
    for check, observed, threshold in checks[1:3]:
        if observed != threshold:
            breaches.append({"check": check, "observed": observed, "threshold": threshold})
    if blocked_tool_executions > policy["maximum_blocked_tool_executions"]:
        breaches.append(
            {
                "check": "maximum_blocked_tool_executions",
                "observed": blocked_tool_executions,
                "threshold": policy["maximum_blocked_tool_executions"],
            }
        )
    if policy["require_database_unchanged"] and report.get("database_unchanged") is not True:
        breaches.append(
            {"check": "require_database_unchanged", "observed": False, "threshold": True}
        )
    if policy["require_unique_decision_traces"] and unique_decision_traces != len(results):
        breaches.append(
            {
                "check": "require_unique_decision_traces",
                "observed": unique_decision_traces,
                "threshold": len(results),
            }
        )
    return {
        "status": "approved" if not breaches else "blocked",
        "model": report.get("model"),
        "model_version": report.get("model_version"),
        "cases": report["cases"],
        "passed": report["passed"],
        "answered_cases": answered,
        "blocked_cases": blocked,
        "tool_executions": report["tool_executions"],
        "blocked_tool_executions": blocked_tool_executions,
        "verified_unique_decision_traces": unique_decision_traces,
        "database_unchanged": report.get("database_unchanged"),
        "breaches": breaches,
        "criteria": policy,
        "interpretation": (
            "Release gate over eight fixed local question fixtures; not a production "
            "accuracy, safety or generative-model evaluation."
        ),
    }


def build_question_release_decision(evaluation_path: Path, policy_path: Path) -> dict:
    report = _load_object(evaluation_path, "question evaluation")
    policy = load_question_release_policy(policy_path)
    result = evaluate_question_release(report, policy)
    evidence = {
        "evaluator_version": RELEASE_EVALUATOR_VERSION,
        "question_evaluation_sha256": _sha256(evaluation_path),
        "policy_sha256": _sha256(policy_path),
        "status": result["status"],
        "breaches": result["breaches"],
    }
    release_id = hashlib.sha256(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**result, "release_evidence": {"release_id": release_id, **evidence}}


def write_question_release_decision(
    evaluation_path: Path, policy_path: Path, output_path: Path
) -> dict:
    result = build_question_release_decision(evaluation_path, policy_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evaluation", type=Path, default=Path("reports/question-evaluation.json")
    )
    parser.add_argument(
        "--policy", type=Path, default=Path("config/question-release-policy.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("reports/question-release.json")
    )
    arguments = parser.parse_args()
    result = write_question_release_decision(
        arguments.evaluation, arguments.policy, arguments.output
    )
    print(
        f"Question-path release: {result['status']}; "
        f"{result['passed']}/{result['cases']} cases; "
        f"{result['blocked_tool_executions']} blocked tool executions"
    )
    return 0 if result["status"] == "approved" else 1


if __name__ == "__main__":
    raise SystemExit(main())
