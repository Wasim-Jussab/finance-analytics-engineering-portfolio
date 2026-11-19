from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from operations_assistant import app as app_module
from operations_assistant.answers import render_answer
from operations_assistant.evaluation import evaluate_answer
from operations_assistant.generate import build_snapshot
from operations_assistant.tools import ToolRequest, execute_tool

PARAMETERS = dict(
    start="2026-09-21", end="2026-09-28",
    baseline_start="2026-09-14", baseline_end="2026-09-21",
)


@pytest.mark.parametrize("mutation", ["region", "count", "no_decrease"])
def test_regional_sentence_is_grounded(tmp_path, mutation):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    result = execute_tool(database, ToolRequest(name="compare_delivery_periods", **PARAMETERS))
    if mutation == "no_decrease":
        # Controlled tool-result boundary, not an observed shipment scenario.
        result["regional_changes"] = []
    answer = render_answer(result)
    assert evaluate_answer(result, answer) == []
    changed = deepcopy(answer)
    if mutation == "no_decrease":
        changed["answer"] = changed["answer"].replace(
            "No region had a decrease", "Every region had a decrease"
        )
    else:
        largest = answer["claims"]["largest_on_time_count_decrease"]
        before = (
            f"{largest['region']} had the largest on-time count decrease "
            f"({largest['on_time_change']:+d})"
        )
        after = (
            f"Wrong-region had the largest on-time count decrease "
            f"({largest['on_time_change']:+d})" if mutation == "region" else
            f"{largest['region']} had the largest on-time count decrease (+999)"
        )
        changed["answer"] = changed["answer"].replace(before, after)
    assert changed["answer"] != answer["answer"]
    assert changed["claims"] == answer["claims"]
    assert changed["evidence"] == answer["evidence"]
    assert "comparison prose regional decrease does not match the approved result" in (
        evaluate_answer(result, changed)
    )


@pytest.mark.parametrize("endpoint", ["/api/answers", "/api/questions"])
def test_api_refuses_wrong_regional_sentence(tmp_path, monkeypatch, endpoint):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    real_render = app_module.render_answer

    def drift(result):
        answer = real_render(result)
        largest = answer["claims"]["largest_on_time_count_decrease"]
        answer["answer"] = answer["answer"].replace(
            f"{largest['region']} had the largest", "Wrong-region had the largest"
        )
        return answer

    request = dict(PARAMETERS)
    request.update(
        {"name": "compare_delivery_periods"} if endpoint == "/api/answers"
        else {"question": "Compare delivery performance between these periods"}
    )
    with TestClient(app_module.create_app(database)) as client:
        assert client.post(endpoint, json=request).status_code == 200
        monkeypatch.setattr(app_module, "render_answer", drift)
        response = client.post(endpoint, json=request)
    assert response.status_code == 500
    assert response.json() == {"detail": "Generated answer failed grounding checks"}
