import hashlib
import json
from pathlib import Path

from operations_assistant.model_artifact import export_model_artifact
from operations_assistant.runtime_readiness import (
    build_runtime_readiness,
    evaluate_runtime_readiness,
)


def _decision(manifest: dict, marker: str) -> dict:
    evidence = {
        "evaluator_version": marker,
        "status": "approved",
        "breaches": [],
    }
    release_id = hashlib.sha256(
        json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "status": "approved",
        "model": manifest["model_name"],
        "model_version": manifest["model_version"],
        "model_artifact_sha256": manifest["artifact_sha256"],
        "breaches": [],
        "release_evidence": {"release_id": release_id, **evidence},
    }


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def test_runtime_readiness_approves_exact_artifact_and_release_identity(
    tmp_path: Path,
) -> None:
    manifest = export_model_artifact(tmp_path / "model")
    result = evaluate_runtime_readiness(
        manifest,
        _decision(manifest, "routing"),
        _decision(manifest, "question"),
    )

    assert result["status"] == "ready"
    assert result["model_artifact_sha256"] == manifest["artifact_sha256"]
    assert result["breaches"] == []
    assert result["inference_boundary"]["generative"] == "not implemented"


def test_runtime_readiness_blocks_mismatched_question_artifact(tmp_path: Path) -> None:
    manifest = export_model_artifact(tmp_path / "model")
    question = _decision(manifest, "question")
    question["model_artifact_sha256"] = "f" * 64

    result = evaluate_runtime_readiness(
        manifest, _decision(manifest, "routing"), question
    )

    assert result["status"] == "blocked"
    assert [breach["check"] for breach in result["breaches"]] == [
        "question_model_artifact_sha256"
    ]


def test_runtime_readiness_blocks_failed_release(tmp_path: Path) -> None:
    manifest = export_model_artifact(tmp_path / "model")
    routing = _decision(manifest, "routing")
    routing["status"] = "blocked"
    routing["breaches"] = [{"check": "fixture"}]
    routing_evidence = {
        "evaluator_version": "routing",
        "status": "blocked",
        "breaches": routing["breaches"],
    }
    routing["release_evidence"] = {
        "release_id": hashlib.sha256(
            json.dumps(
                routing_evidence, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest(),
        **routing_evidence,
    }

    result = evaluate_runtime_readiness(
        manifest, routing, _decision(manifest, "question")
    )

    assert result["status"] == "blocked"
    assert result["breaches"][0]["check"] == "routing_release_approved"


def test_runtime_readiness_build_verifies_persisted_artifact(tmp_path: Path) -> None:
    model = tmp_path / "model"
    manifest = export_model_artifact(model)
    routing = tmp_path / "routing.json"
    question = tmp_path / "question.json"
    _write(routing, _decision(manifest, "routing"))
    _write(question, _decision(manifest, "question"))

    result = build_runtime_readiness(model, routing, question)

    assert result["status"] == "ready"
