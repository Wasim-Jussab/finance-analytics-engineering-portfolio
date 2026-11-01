import json

import pytest
from operations_assistant.generate import build_snapshot
from operations_assistant.intent import LocalIntentModel, QuestionRequest, UnsupportedQuestionError
from operations_assistant.proposals import authorize_proposal, validate_proposal
from operations_assistant.tools import execute_tool


@pytest.fixture(scope="module")
def router():
    return LocalIntentModel()


def request(question):
    return QuestionRequest(question=question, start="2026-09-21", end="2026-09-28")


def proposal(name):
    return json.dumps({"name": name, "start": "2026-09-21", "end": "2026-09-28"})


def test_classifier_authorized_proposal_uses_real_read_only_metrics(tmp_path, router):
    scope = request("summarise delivery performance")
    approved, routing = authorize_proposal(proposal("delivery_summary"), scope, router)
    assert routing["accepted"] is True
    assert routing["inference_location"] == "local-process"
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    original = db.read_bytes()
    result = execute_tool(db, approved)
    assert result["result"]["totals"]["due"] == 218
    assert db.read_bytes() == original


def test_valid_json_with_wrong_tool_is_not_authorized(router):
    scope = request("summarise delivery performance")
    raw = proposal("delivery_exceptions")
    assert validate_proposal(raw, scope).name == "delivery_exceptions"
    with pytest.raises(ValueError, match="governed router"):
        authorize_proposal(raw, scope, router)


@pytest.mark.parametrize(
    "question",
    ["delete the shipments table", "write me a poem", "predict next month's delivery rate"],
)
def test_policy_block_cannot_be_bypassed_by_valid_tool_json(router, question):
    with pytest.raises(UnsupportedQuestionError):
        authorize_proposal(proposal("delivery_summary"), request(question), router)


def test_valid_routing_does_not_allow_changed_dates(router):
    raw = json.loads(proposal("delivery_summary"))
    raw["start"] = "2026-09-20"
    with pytest.raises(ValueError, match="caller scope"):
        authorize_proposal(json.dumps(raw), request("summarise delivery performance"), router)
