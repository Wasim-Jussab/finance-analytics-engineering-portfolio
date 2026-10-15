"""Write, verify and load the trusted local intent-model artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import joblib
import sklearn
from sklearn.pipeline import Pipeline

from operations_assistant.model_adapter import (
    TRAINING_EXAMPLES,
    TfidfLogisticIntentAdapter,
)

ARTIFACT_VERSION = "1.0.0"
MODEL_FILENAME = "intent-model.joblib"
MANIFEST_FILENAME = "model-manifest.json"
EXPECTED_LABELS = ["compare_delivery_periods", "delivery_summary", "unsupported"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_manifest(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read model manifest {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError("Model manifest must contain a JSON object")
    return value


def _validate_directory(directory: Path) -> None:
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f"Model artifact must be a real directory: {directory}")
    actual = {path.name for path in directory.iterdir()}
    expected = {MODEL_FILENAME, MANIFEST_FILENAME}
    if actual != expected:
        raise ValueError("Model artifact contains missing or unexpected files")
    if any(path.is_symlink() for path in directory.iterdir()):
        raise ValueError("Model artifact files must not be symbolic links")


def export_model_artifact(directory: Path) -> dict:
    """Fit locally and atomically publish a fingerprinted model artifact."""

    adapter = TfidfLogisticIntentAdapter()
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{directory.name}.", dir=directory.parent) as raw:
        staging = Path(raw)
        model_path = staging / MODEL_FILENAME
        joblib.dump(adapter.pipeline, model_path)
        manifest = {
            "artifact_version": ARTIFACT_VERSION,
            "artifact_file": MODEL_FILENAME,
            "artifact_sha256": _sha256(model_path),
            "adapter_name": adapter.adapter_name,
            "model_name": adapter.model_name,
            "model_version": adapter.model_version,
            "sklearn_version": sklearn.__version__,
            "training_example_count": len(TRAINING_EXAMPLES),
            "labels": EXPECTED_LABELS,
            "inference_location": adapter.inference_location,
            "network_required": adapter.network_required,
            "interpretation": (
                "Locally trained intent classifier; trusted local serialization only, "
                "not a generative model."
            ),
        }
        (staging / MANIFEST_FILENAME).write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        if directory.exists():
            verify_model_artifact(directory)
            if (directory / MODEL_FILENAME).read_bytes() == model_path.read_bytes():
                return _read_manifest(directory / MANIFEST_FILENAME)
            raise ValueError("Existing model artifact differs; remove it before replacement")
        os.rename(staging, directory)
    return verify_model_artifact(directory)


def _load_verified_pipeline(directory: Path) -> tuple[dict, Pipeline]:
    _validate_directory(directory)
    manifest = _read_manifest(directory / MANIFEST_FILENAME)
    adapter = TfidfLogisticIntentAdapter
    expected_version = hashlib.sha256(
        json.dumps(adapter.specification(), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:12]
    expected_metadata = {
        "artifact_version": ARTIFACT_VERSION,
        "artifact_file": MODEL_FILENAME,
        "adapter_name": adapter.adapter_name,
        "model_name": adapter.model_name,
        "model_version": expected_version,
        "sklearn_version": sklearn.__version__,
        "training_example_count": len(TRAINING_EXAMPLES),
        "labels": EXPECTED_LABELS,
        "inference_location": adapter.inference_location,
        "network_required": adapter.network_required,
    }
    for key, expected in expected_metadata.items():
        if manifest.get(key) != expected:
            raise ValueError(f"Model manifest has incompatible {key}")
    model_path = directory / MODEL_FILENAME
    if manifest.get("artifact_sha256") != _sha256(model_path):
        raise ValueError("Model artifact fingerprint does not match its manifest")
    pipeline = joblib.load(model_path)
    if not isinstance(pipeline, Pipeline):
        raise ValueError("Model artifact does not contain the expected pipeline")
    labels = sorted(str(value) for value in pipeline.classes_)
    if labels != EXPECTED_LABELS:
        raise ValueError("Model artifact classifier labels do not match the approved labels")
    return manifest, pipeline


def verify_model_artifact(directory: Path) -> dict:
    """Verify bytes and metadata before deserializing the trusted local artifact."""

    manifest, _ = _load_verified_pipeline(directory)
    return manifest


def load_model_artifact(directory: Path) -> TfidfLogisticIntentAdapter:
    """Verify then load a locally generated and trusted classifier artifact."""

    manifest, pipeline = _load_verified_pipeline(directory)
    return TfidfLogisticIntentAdapter(
        pipeline=pipeline,
        artifact_sha256=manifest["artifact_sha256"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory", type=Path, default=Path("artifacts/local-intent-model")
    )
    parser.add_argument("--verify", action="store_true")
    arguments = parser.parse_args()
    if arguments.verify:
        result = verify_model_artifact(arguments.directory)
        verb = "verified"
    else:
        result = export_model_artifact(arguments.directory)
        verb = "exported"
    print(
        f"Local intent model {verb}: {result['model_version']} "
        f"({result['artifact_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
