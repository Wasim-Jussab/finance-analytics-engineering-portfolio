from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from operations_assistant import proposal_demo
from operations_assistant.app import create_app
from operations_assistant.decision_trace import verify_answer_binding, verify_decision_trace
from operations_assistant.generate import build_snapshot
from operations_assistant.model_artifact import export_model_artifact


def test_demo_reconciles_weekly_cohorts_with_grounded_evidence(tmp_path, monkeypatch):
    artifact = tmp_path / "artifact"
    manifest = export_model_artifact(artifact)
    # The package gate exercises the real release files; isolate the answer seam here.
    monkeypatch.setattr(
        proposal_demo,
        "build_runtime_readiness",
        lambda *_: {"status": "ready", "model_artifact_sha256": manifest["artifact_sha256"]},
    )
    result = proposal_demo.run_demo(artifact, tmp_path, tmp_path)
    baseline, current = (result["claims"][key] for key in ("baseline", "current"))
    assert (baseline["due"], baseline["on_time"]) == (213, 176)
    assert (current["due"], current["on_time"], current["cancelled"]) == (218, 153, 6)
    assert (
        current["due"] == current["on_time"] + current["late_delivered"] + current["overdue_open"]
    )
    expected_change = (153 / 218 - 176 / 213) * 100
    assert result["claims"]["change"]["on_time_rate_change_percentage_points"] == pytest.approx(
        expected_change
    )
    assert f"{expected_change:+.2f} percentage points" in result["answer"]
    assert result["evidence"]["request"]["name"] == "compare_delivery_periods"
    assert result["evidence"]["evidence_id"] in result["answer"]
    assert result["routing"]["model_artifact_sha256"] == manifest["artifact_sha256"]
    assert result["generative_inference"] is False
    trace = result["decision_trace"]
    verify_decision_trace(trace)
    assert trace["evidence_id"] == result["evidence"]["evidence_id"]
    assert "question" not in trace["parameters"]

    database = tmp_path / "api.duckdb"
    build_snapshot(database)
    with TestClient(create_app(database=database, model_artifact=artifact)) as client:
        response = client.post(
            "/api/questions",
            json={
                **trace["parameters"],
                "question": "How does the current week compare with the prior week?",
            },
        )
    assert response.status_code == 200
    assert response.json()["claims"] == result["claims"]
    assert response.json()["decision_trace"] == trace
    verify_answer_binding(trace, response.json())

    for field, change, message in (
        ("claims", {"current": {"on_time": 154}}, "claims"),
        ("evidence", {"evidence_id": "different-evidence"}, "evidence_id"),
        ("evidence", {"contract_version": "other-contract"}, "contract_version"),
        (
            "evidence",
            {"request": {**result["evidence"]["request"], "region": "North"}},
            "tool request",
        ),
    ):
        edited = deepcopy(result)
        edited[field].update(change)
        # The standalone trace still verifies; the answer paired with it does not.
        verify_decision_trace(trace)
        with pytest.raises(ValueError, match=message):
            verify_answer_binding(trace, edited)


def test_blocked_readiness_stops_before_loading_classifier_for_routing(tmp_path, monkeypatch):
    monkeypatch.setattr(
        proposal_demo,
        "build_runtime_readiness",
        lambda *_: {"status": "blocked", "breaches": [{"check": "question_release_approved"}]},
    )

    def unexpected_load(*_):
        pytest.fail("Blocked release must not load a classifier for routing")

    monkeypatch.setattr(proposal_demo, "load_model_artifact", unexpected_load)
    with pytest.raises(ValueError, match="question_release_approved"):
        proposal_demo.run_demo(tmp_path, tmp_path, tmp_path)


def test_classifier_changed_after_readiness_stops_before_planning(tmp_path, monkeypatch):
    monkeypatch.setattr(
        proposal_demo,
        "build_runtime_readiness",
        lambda *_: {"status": "ready", "model_artifact_sha256": "a" * 64},
    )
    monkeypatch.setattr(
        proposal_demo,
        "load_model_artifact",
        lambda *_: SimpleNamespace(artifact_sha256="b" * 64),
    )

    def unexpected_plan(*_):
        pytest.fail("An unapproved artifact must not reach planning")

    monkeypatch.setattr(proposal_demo, "LocalIntentModel", unexpected_plan)
    with pytest.raises(ValueError, match="differs from the approved artifact"):
        proposal_demo.run_demo(tmp_path, tmp_path, tmp_path)
