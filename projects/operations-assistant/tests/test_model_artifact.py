import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from operations_assistant.adversarial_evaluation import run_adversarial_evaluation
from operations_assistant.app import create_app
from operations_assistant.generate import build_snapshot
from operations_assistant.intent import LocalIntentModel
from operations_assistant.intent_evaluation import run_intent_evaluation
from operations_assistant.model_artifact import (
    MODEL_FILENAME,
    export_model_artifact,
    load_model_artifact,
    verify_model_artifact,
)


def test_exported_model_reloads_with_same_prediction(tmp_path: Path) -> None:
    directory = tmp_path / "model"
    manifest = export_model_artifact(directory)

    loaded = load_model_artifact(directory)
    fresh = LocalIntentModel().predict("Compare delivery performance with last week")
    restored = LocalIntentModel(adapter=loaded).predict(
        "Compare delivery performance with last week"
    )

    for key in fresh:
        if key != "model_artifact_sha256":
            assert restored[key] == fresh[key]
    assert restored["model_artifact_sha256"] == manifest["artifact_sha256"]
    assert len(manifest["artifact_sha256"]) == 64
    assert manifest["network_required"] is False


def test_model_artifact_export_is_idempotent(tmp_path: Path) -> None:
    directory = tmp_path / "model"
    first = export_model_artifact(directory)
    second = export_model_artifact(directory)

    assert second == first


def test_model_artifact_rejects_changed_bytes(tmp_path: Path) -> None:
    directory = tmp_path / "model"
    export_model_artifact(directory)
    with (directory / MODEL_FILENAME).open("ab") as model_file:
        model_file.write(b"changed")

    with pytest.raises(ValueError, match="fingerprint"):
        load_model_artifact(directory)


def test_model_artifact_rejects_incompatible_library_version(tmp_path: Path) -> None:
    directory = tmp_path / "model"
    export_model_artifact(directory)
    manifest_path = directory / "model-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sklearn_version"] = "0.0.0"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="incompatible sklearn_version"):
        verify_model_artifact(directory)


def test_model_artifact_rejects_unexpected_file(tmp_path: Path) -> None:
    directory = tmp_path / "model"
    export_model_artifact(directory)
    (directory / "extra.txt").write_text("unexpected", encoding="utf-8")

    with pytest.raises(ValueError, match="missing or unexpected"):
        verify_model_artifact(directory)


def test_question_api_executes_with_verified_model_artifact(tmp_path: Path) -> None:
    directory = tmp_path / "model"
    manifest = export_model_artifact(directory)
    database = tmp_path / "operations.duckdb"
    build_snapshot(database)
    client = TestClient(create_app(database, model_artifact=directory))

    response = client.post(
        "/api/questions",
        json={
            "question": "Show delivery performance for this week",
            "start": "2026-09-21",
            "end": "2026-09-28",
        },
    )

    assert response.status_code == 200
    assert response.json()["routing"]["model_version"] == manifest["model_version"]
    assert response.json()["routing"]["model_artifact_sha256"] == manifest["artifact_sha256"]
    assert response.json()["mode"] == "deterministic-template; local intent inference only"
    assert response.json()["evidence"]["mode"] == "deterministic metric computation"


def test_verified_artifact_executes_both_routing_evaluations(tmp_path: Path) -> None:
    directory = tmp_path / "model"
    manifest = export_model_artifact(directory)
    model = LocalIntentModel(adapter=load_model_artifact(directory))

    held_out = run_intent_evaluation(model)
    adversarial = run_adversarial_evaluation(model)

    assert held_out["passed"] == held_out["cases"] == 18
    assert adversarial["passed"] == adversarial["cases"] == 27
    assert held_out["model_artifact_sha256"] == manifest["artifact_sha256"]
    assert adversarial["model_artifact_sha256"] == manifest["artifact_sha256"]
