import json
import subprocess
import sys
from pathlib import Path

import pytest
from operations_assistant.adversarial_evaluation import run_adversarial_evaluation
from operations_assistant.intent_evaluation import run_intent_evaluation


@pytest.mark.parametrize("case", ["valid", "missing_audit", "coherent_false_flags"])
def test_release_command_checks_audit_before_publishing_decision(tmp_path, case):
    report = run_intent_evaluation()
    if case == "missing_audit":
        report.pop("reference_training_overlap")
    elif case == "coherent_false_flags":
        row = next(r for r in report["results"] if r["overlaps_reference_training"])
        row["overlaps_reference_training"] = False
        report["reference_training_overlap"]["overlapping_cases"] -= 1
        report["reference_training_overlap"]["non_overlapping_cases"] += 1
    intent, adversarial, output = (
        tmp_path / name for name in ["intent.json", "adv.json", "out.json"]
    )
    intent.write_text(json.dumps(report), encoding="utf-8")
    adversarial.write_text(json.dumps(run_adversarial_evaluation()), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "operations_assistant.routing_release",
            "--held-out",
            str(intent),
            "--adversarial",
            str(adversarial),
            "--policy",
            str(Path("config/routing-release-policy.json").resolve()),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if case == "valid":
        assert result.returncode == 0, result.stderr
        decision = json.loads(output.read_text(encoding="utf-8"))
        assert decision["status"] == "approved"
        assert decision["release_evidence"]["evaluator_version"] == "1.4.0"
        assert decision["evaluation_scope"]["independent_holdout_claim_supported"] is False
    else:
        assert result.returncode != 0
        assert "overlap" in result.stderr.lower()
        assert not output.exists()
