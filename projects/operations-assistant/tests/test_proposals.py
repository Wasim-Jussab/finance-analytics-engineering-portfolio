import json

import pytest
from operations_assistant.generate import build_snapshot
from operations_assistant.intent import QuestionRequest
from operations_assistant.proposals import validate_proposal
from operations_assistant.tools import execute_tool


def scope():
    return QuestionRequest(
        question="List overdue shipment exceptions",
        start="2026-09-21",
        end="2026-09-28",
        outcome="overdue_open",
        limit=7,
    )


def payload():
    return {
        "name": "delivery_exceptions",
        "start": "2026-09-21",
        "end": "2026-09-28",
        "outcome": "overdue_open",
        "limit": 7,
    }


def test_validated_proposal_executes_only_through_existing_read_only_tool(tmp_path):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    before = db.read_bytes()
    request = validate_proposal(json.dumps(payload()), scope())
    result = execute_tool(db, request)
    assert result["exception_count"] == 21
    assert len(result["rows"]) == 7
    assert result["evidence"]["request"]["outcome"] == "overdue_open"
    assert db.read_bytes() == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("start", "2026-09-20"),
        ("limit", 100),
        ("outcome", "late_delivered"),
        ("region", "North"),
        ("offset", 7),
        ("sql", "delete from shipments"),
        ("name", "execute_sql"),
    ],
)
def test_model_cannot_change_scope_or_add_capabilities(field, value):
    proposal = {**payload(), field: value}
    with pytest.raises(ValueError):
        validate_proposal(json.dumps(proposal), scope())


@pytest.mark.parametrize(
    "raw",
    [
        "[]",
        "null",
        '{"name":"delivery_summary","name":"delivery_exceptions"}',
        '{"limit":NaN}',
        "```json\n{}\n```",
        "x" * 4097,
    ],
)
def test_non_json_ambiguous_or_oversized_output_is_rejected(raw):
    with pytest.raises(ValueError):
        validate_proposal(raw, scope())


@pytest.mark.parametrize("name", ["delivery_summary", "compare_delivery_periods"])
def test_other_approved_tools_preserve_explicit_periods(name):
    arguments = {"start": "2026-09-21", "end": "2026-09-28"}
    if name == "compare_delivery_periods":
        arguments.update(baseline_start="2026-09-14", baseline_end="2026-09-21")
    trusted = QuestionRequest(question="Show delivery performance", **arguments)
    assert validate_proposal(json.dumps({"name": name, **arguments}), trusted).name == name


def test_snapshot_pin_cannot_be_dropped():
    trusted = scope().model_copy(update={"expected_snapshot_id": "a" * 64})
    with pytest.raises(ValueError, match="caller scope"):
        validate_proposal(json.dumps(payload()), trusted)
