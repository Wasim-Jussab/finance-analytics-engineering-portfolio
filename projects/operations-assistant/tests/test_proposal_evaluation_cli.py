import json
import subprocess
import sys

from operations_assistant.model_artifact import MODEL_FILENAME, export_model_artifact


def test_cli_binds_report_to_verified_artifact_and_rejects_tampered_bytes(tmp_path):
    artifact = tmp_path / "model"
    manifest = export_model_artifact(artifact)
    report = tmp_path / "evaluation.json"
    command = [
        sys.executable,
        "-m",
        "operations_assistant.proposal_evaluation",
        "--model-artifact",
        str(artifact),
        "--output",
        str(report),
    ]
    successful = subprocess.run(command, capture_output=True, text=True, check=False)
    assert successful.returncode == 0, successful.stderr
    result = json.loads(report.read_text())
    assert result["model_artifact_sha256"] == manifest["artifact_sha256"]
    assert result["passed"] == result["cases"] == 18
    assert result["generative_inference"] is False
    assert result["tools_executed"] is False
    original_report = report.read_bytes()
    # Corrupt a locally generated fixture; never load untrusted serialization.
    model = artifact / MODEL_FILENAME
    model.write_bytes(model.read_bytes() + b"tampered-test-fixture")
    rejected = subprocess.run(command, capture_output=True, text=True, check=False)
    assert rejected.returncode != 0
    assert rejected.stdout == ""
    assert report.read_bytes() == original_report
    assert "fingerprint" in rejected.stderr
