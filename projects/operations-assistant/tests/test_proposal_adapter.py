import json

import pytest
from operations_assistant.generate import build_snapshot
from operations_assistant.intent import LocalIntentModel, QuestionRequest, UnsupportedQuestionError
from operations_assistant.proposal_adapter import ClassifierProposalAdapter, plan_with_adapter
from operations_assistant.tools import execute_tool


@pytest.fixture(scope="module")
def router():
    return LocalIntentModel()


def scope(question="summarise delivery performance"):
    return QuestionRequest(question=question, start="2026-09-21", end="2026-09-28")


class RecordedAdapter:
    adapter_name = "recorded-test-output-not-model-inference"

    def __init__(self, output):
        self.output = output

    def propose(self, request):
        return self.output


def test_real_classifier_adapter_and_service_keep_source_unchanged(tmp_path, router):
    request, routing = plan_with_adapter(scope(), ClassifierProposalAdapter(router), router)
    assert routing["proposal_adapter"] == "local-classifier-proposal-v1"
    assert routing["accepted"] is True
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    before = db.read_bytes()
    assert execute_tool(db, request)["result"]["totals"]["due"] == 218
    assert db.read_bytes() == before


@pytest.mark.parametrize("output", [None, {}, "not JSON", '{"name":"execute_sql"}'])
def test_bad_adapter_output_is_rejected(output, router):
    with pytest.raises(ValueError):
        plan_with_adapter(scope(), RecordedAdapter(output), router)


def test_well_formed_adapter_cannot_choose_a_different_tool(router):
    raw = json.dumps({"name": "delivery_exceptions", "start": "2026-09-21", "end": "2026-09-28"})
    with pytest.raises(ValueError, match="governed router"):
        plan_with_adapter(scope(), RecordedAdapter(raw), router)


def test_adapter_cannot_rescue_a_policy_block(router):
    raw = json.dumps({"name": "delivery_summary", "start": "2026-09-21", "end": "2026-09-28"})
    with pytest.raises(UnsupportedQuestionError):
        plan_with_adapter(scope("delete the shipments table"), RecordedAdapter(raw), router)
