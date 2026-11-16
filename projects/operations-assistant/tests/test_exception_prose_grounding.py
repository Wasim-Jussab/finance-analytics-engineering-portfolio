from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from operations_assistant import app as app_module
from operations_assistant.answers import render_answer
from operations_assistant.evaluation import evaluate_answer
from operations_assistant.generate import build_snapshot
from operations_assistant.tools import ToolRequest, execute_tool


@pytest.mark.parametrize(
    ("original", "edited", "claim"),
    [
        ("contains 65 ", "contains 999 ", "population"),
        ("Returning 5 ", "Returning 999 ", "page"),
        ("from offset 0", "from offset 99", "page"),
        ("FIRST_SHIPMENT_ID", "NOT-IN-RESULT", "rows"),
        ("request offset 5", "request offset 999", "pagination"),
        (
            "Further rows remain; request offset 5 for the next page.",
            "The complete exception set is returned.",
            "pagination",
        ),
    ],
)
def test_exception_prose_edits_fail_with_unchanged_claims(tmp_path, original, edited, claim):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    result = execute_tool(
        database,
        ToolRequest(
            name="delivery_exceptions",
            start="2026-09-21",
            end="2026-09-28",
            limit=5,
        ),
    )
    answer = render_answer(result)
    assert evaluate_answer(result, answer) == []
    if original == "FIRST_SHIPMENT_ID":
        original = result["rows"][0]["shipment_id"]
    changed = deepcopy(answer)
    assert original in changed["answer"]
    changed["answer"] = changed["answer"].replace(original, edited)
    assert changed["claims"] == answer["claims"]
    assert changed["evidence"] == answer["evidence"]
    assert evaluate_answer(result, changed) == [
        f"exception prose {claim} does not match the approved tool result"
    ]


@pytest.mark.parametrize("endpoint", ["/api/answers", "/api/questions"])
def test_api_refuses_wrong_next_offset(tmp_path, monkeypatch, endpoint):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    real_render = app_module.render_answer

    def edited_render(result):
        answer = real_render(result)
        assert "request offset 5" in answer["answer"]
        answer["answer"] = answer["answer"].replace("request offset 5", "request offset 999")
        return answer

    request = {"start": "2026-09-21", "end": "2026-09-28", "limit": 5}
    request.update(
        {"name": "delivery_exceptions"}
        if endpoint == "/api/answers"
        else {"question": "List the five worst delivery exceptions"}
    )
    with TestClient(app_module.create_app(database)) as client:
        assert client.post(endpoint, json=request).status_code == 200
        monkeypatch.setattr(app_module, "render_answer", edited_render)
        refused = client.post(endpoint, json=request)
    assert refused.status_code == 500
    assert refused.json() == {"detail": "Generated answer failed grounding checks"}
