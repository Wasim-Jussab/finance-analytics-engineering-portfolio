from copy import deepcopy

import pytest
from operations_assistant.answers import render_answer
from operations_assistant.evaluation import evaluate_answer
from operations_assistant.generate import build_snapshot
from operations_assistant.tools import ToolRequest, execute_tool


@pytest.mark.parametrize(
    ("original", "edited", "claim"),
    [
        ("218 non-cancelled", "999 non-cancelled", "due"),
        ("153 on time,", "999 on time,", "on_time"),
        ("44 delivered late", "999 delivered late", "late_delivered"),
        ("21 still open", "999 still open", "overdue_open"),
        ("6 cancelled rows", "999 cancelled rows", "cancelled"),
        ("rate is 70.18%;", "rate is 99.99%;", "on_time_rate"),
    ],
)
def test_changed_prose_fails_even_with_unchanged_claims_and_evidence(
    tmp_path, original, edited, claim
):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    result = execute_tool(
        database,
        ToolRequest(name="delivery_summary", start="2026-09-21", end="2026-09-28"),
    )
    answer = render_answer(result)
    assert evaluate_answer(result, answer) == []
    changed = deepcopy(answer)
    assert original in changed["answer"]
    changed["answer"] = changed["answer"].replace(original, edited)
    assert changed["claims"] == answer["claims"]
    assert changed["evidence"] == answer["evidence"]
    assert evaluate_answer(result, changed) == [
        f"summary prose {claim} does not match the approved tool result"
    ]
