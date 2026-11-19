from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from operations_assistant import app as app_module
from operations_assistant.answers import render_answer
from operations_assistant.evaluation import evaluate_answer
from operations_assistant.generate import build_snapshot
from operations_assistant.tools import ToolRequest, execute_tool

TOOLS = (
    ("delivery_summary", "Give me delivery totals for this period"),
    ("compare_delivery_periods", "Compare delivery performance between these periods"),
    ("delivery_exceptions", "List the five worst delivery exceptions"),
)


def parameters(name):
    request = {"start": "2026-09-21", "end": "2026-09-28"}
    if name == "compare_delivery_periods":
        request.update(baseline_start="2026-09-14", baseline_end="2026-09-21")
    return request


@pytest.mark.parametrize(("name", "_question"), TOOLS)
@pytest.mark.parametrize("field", ["region", "snapshot time"])
def test_prose_scope_drift_fails_with_unchanged_claims(tmp_path, name, _question, field):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    result = execute_tool(database, ToolRequest(name=name, **parameters(name)))
    answer = render_answer(result)
    assert evaluate_answer(result, answer) == []
    changed = deepcopy(answer)
    if field == "region":
        changed["answer"] = changed["answer"].replace("For all regions, ", "For North, ")
    else:
        changed["answer"] = changed["answer"].replace("2026-09-28T00:00:00+00:00", "2025-01-01")
    assert changed["answer"] != answer["answer"]
    assert changed["claims"] == answer["claims"]
    assert changed["evidence"] == answer["evidence"]
    assert f"answer prose {field} does not match the approved tool result" in evaluate_answer(
        result, changed
    )


@pytest.mark.parametrize(("name", "question"), TOOLS)
@pytest.mark.parametrize("endpoint", ["/api/answers", "/api/questions"])
def test_api_refuses_wrong_snapshot_time(tmp_path, monkeypatch, name, question, endpoint):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    real_render = app_module.render_answer

    def edited_render(result):
        answer = real_render(result)
        assert "2026-09-28T00:00:00+00:00" in answer["answer"]
        answer["answer"] = answer["answer"].replace("2026-09-28T00:00:00+00:00", "2025-01-01")
        return answer

    request = parameters(name)
    request.update({"name": name} if endpoint == "/api/answers" else {"question": question})
    with TestClient(app_module.create_app(database)) as client:
        assert client.post(endpoint, json=request).status_code == 200
        monkeypatch.setattr(app_module, "render_answer", edited_render)
        refused = client.post(endpoint, json=request)
    assert refused.status_code == 500
    assert refused.json() == {"detail": "Generated answer failed grounding checks"}
