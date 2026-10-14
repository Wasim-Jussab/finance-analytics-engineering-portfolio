from pathlib import Path

from fastapi.testclient import TestClient
from operations_assistant.app import create_app
from operations_assistant.model_artifact import export_model_artifact


def test_model_endpoint_discloses_in_memory_inference_boundary() -> None:
    result = TestClient(create_app()).get("/api/model").json()

    assert result["classification_inference"] == {
        "implemented": True,
        "scope": "intent classification only",
        "location": "local-process",
        "network_required": False,
    }
    assert result["generative_inference"] == {
        "implemented": False,
        "answer_mode": "deterministic template",
    }
    assert result["artifact"] == {
        "mode": "in-memory development fit",
        "sha256": None,
    }
    assert result["approved_labels"] == [
        "compare_delivery_periods",
        "delivery_summary",
        "unsupported",
    ]


def test_model_endpoint_identifies_verified_persisted_artifact(tmp_path: Path) -> None:
    directory = tmp_path / "model"
    manifest = export_model_artifact(directory)

    result = TestClient(create_app(model_artifact=directory)).get("/api/model").json()

    assert result["artifact"] == {
        "mode": "verified persisted artifact",
        "sha256": manifest["artifact_sha256"],
    }
    assert result["model_version"] == manifest["model_version"]
    assert result["confidence_threshold"] == 0.38
