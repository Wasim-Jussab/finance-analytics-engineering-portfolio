"""Bind the verified runtime artifact to approved routing and question evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from operations_assistant.model_artifact import verify_model_artifact

READINESS_EVALUATOR_VERSION = "1.0.0"


def _load_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read {label} {path}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label.capitalize()} must contain a JSON object")
    return value


def _release_id(decision: dict, label: str) -> str:
    evidence = decision.get("release_evidence")
    if not isinstance(evidence, dict):
        raise ValueError(f"{label.capitalize()} release evidence is missing")
    release_id = evidence.get("release_id")
    if (
        not isinstance(release_id, str)
        or len(release_id) != 64
        or any(character not in "0123456789abcdef" for character in release_id)
    ):
        raise ValueError(f"{label.capitalize()} release ID is invalid")
    identity = {key: value for key, value in evidence.items() if key != "release_id"}
    expected_id = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if release_id != expected_id:
        raise ValueError(f"{label.capitalize()} release ID does not match its evidence")
    if evidence.get("status") != decision.get("status"):
        raise ValueError(f"{label.capitalize()} release status evidence is inconsistent")
    if evidence.get("breaches") != decision.get("breaches"):
        raise ValueError(f"{label.capitalize()} release breach evidence is inconsistent")
    return release_id


def evaluate_runtime_readiness(
    manifest: dict, routing_release: dict, question_release: dict
) -> dict:
    """Return readiness only when both gates approve the exact runtime bytes."""

    model = manifest.get("model_name")
    version = manifest.get("model_version")
    artifact_sha256 = manifest.get("artifact_sha256")
    if not all(isinstance(value, str) and value for value in (model, version, artifact_sha256)):
        raise ValueError("Verified model manifest is missing runtime identity")

    releases = {
        "routing": routing_release,
        "question": question_release,
    }
    release_ids = {
        label: _release_id(decision, label) for label, decision in releases.items()
    }
    breaches = []
    for label, decision in releases.items():
        if decision.get("status") != "approved" or decision.get("breaches") != []:
            breaches.append(
                {
                    "check": f"{label}_release_approved",
                    "observed": decision.get("status"),
                    "threshold": "approved",
                }
            )
        for field, expected in (
            ("model", model),
            ("model_version", version),
            ("model_artifact_sha256", artifact_sha256),
        ):
            if decision.get(field) != expected:
                breaches.append(
                    {
                        "check": f"{label}_{field}",
                        "observed": decision.get(field),
                        "threshold": expected,
                    }
                )

    return {
        "status": "ready" if not breaches else "blocked",
        "evaluator_version": READINESS_EVALUATOR_VERSION,
        "model": model,
        "model_version": version,
        "model_artifact_sha256": artifact_sha256,
        "routing_release_id": release_ids["routing"],
        "question_release_id": release_ids["question"],
        "breaches": breaches,
        "inference_boundary": {
            "classification": "local intent classification only",
            "generative": "not implemented",
            "answers": "deterministic templates over approved read-only tools",
        },
        "interpretation": (
            "Local deployment evidence for the exact evaluated classifier bytes; "
            "not a production accuracy, security or generative-model approval."
        ),
    }


def build_runtime_readiness(
    model_artifact: Path, routing_release_path: Path, question_release_path: Path
) -> dict:
    manifest = verify_model_artifact(model_artifact)
    routing = _load_object(routing_release_path, "routing release decision")
    question = _load_object(question_release_path, "question release decision")
    return evaluate_runtime_readiness(manifest, routing, question)


def write_runtime_readiness(
    model_artifact: Path,
    routing_release_path: Path,
    question_release_path: Path,
    output_path: Path,
) -> dict:
    result = build_runtime_readiness(
        model_artifact, routing_release_path, question_release_path
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(f"{output_path.suffix}.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-artifact", type=Path, default=Path("artifacts/local-intent-model")
    )
    parser.add_argument(
        "--routing-release", type=Path, default=Path("reports/routing-release.json")
    )
    parser.add_argument(
        "--question-release", type=Path, default=Path("reports/question-release.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("reports/runtime-readiness.json")
    )
    arguments = parser.parse_args()
    result = write_runtime_readiness(
        arguments.model_artifact,
        arguments.routing_release,
        arguments.question_release,
        arguments.output,
    )
    print(
        f"Runtime readiness: {result['status']}; "
        f"model {result['model_version']} ({result['model_artifact_sha256']})"
    )
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
