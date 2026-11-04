import json

from operations_assistant.intent import LocalIntentModel
from operations_assistant.proposal_evaluation import evaluate


def test_executed_baseline_passes_reused_cases_without_claiming_generation():
    report = evaluate(LocalIntentModel())
    assert report["cases"] == report["passed"] == 18
    assert report["failed"] == 0
    assert report["generative_inference"] is False
    assert report["tools_executed"] is False
    assert all("question" not in row for row in report["results"])


def test_wrong_producer_does_not_get_a_passing_report():
    class WrongAdapter:
        adapter_name = "test-double-not-inference"

        def propose(self, scope):
            return json.dumps(
                {"name": "delivery_summary", "start": "2026-09-21", "end": "2026-09-28"}
            )

    report = evaluate(LocalIntentModel(), WrongAdapter())
    assert report["failed"] > 0
    assert report["passed"] < report["cases"]
    assert any(row["error_type"] for row in report["results"])
