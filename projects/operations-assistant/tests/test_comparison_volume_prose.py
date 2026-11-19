import re
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from operations_assistant import app as app_module
from operations_assistant.answers import render_answer
from operations_assistant.evaluation import evaluate_answer
from operations_assistant.generate import build_snapshot
from operations_assistant.tools import ToolRequest, execute_tool

PARAMETERS = {
    "start": "2026-09-21",
    "end": "2026-09-28",
    "baseline_start": "2026-09-14",
    "baseline_end": "2026-09-21",
}
LABELS = ("Due volume changed by", "late deliveries by", "overdue-open shipments by")


def alter_volume(answer, label):
    changed = deepcopy(answer)
    changed["answer"] = re.sub(
        re.escape(label) + r" ([+-]\d+)",
        lambda match: f"{label} {int(match.group(1)) + 1:+d}",
        changed["answer"],
        count=1,
    )
    assert changed["answer"] != answer["answer"]
    return changed


@pytest.mark.parametrize("label", LABELS)
def test_volume_prose_drift_is_rejected(tmp_path, label):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    result = execute_tool(database, ToolRequest(name="compare_delivery_periods", **PARAMETERS))
    answer = render_answer(result)
    assert evaluate_answer(result, answer) == []
    changed = alter_volume(answer, label)
    assert changed["claims"] == answer["claims"]
    assert changed["evidence"] == answer["evidence"]
    assert "comparison prose volume changes do not match the approved tool result" in (
        evaluate_answer(result, changed)
    )


@pytest.mark.parametrize("label", LABELS)
@pytest.mark.parametrize("endpoint", ["/api/answers", "/api/questions"])
def test_api_refuses_volume_prose_drift(tmp_path, monkeypatch, label, endpoint):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    real_render = app_module.render_answer
    request = dict(PARAMETERS)
    request.update(
        {"name": "compare_delivery_periods"} if endpoint == "/api/answers"
        else {"question": "Compare delivery performance between these periods"}
    )
    with TestClient(app_module.create_app(database)) as client:
        assert client.post(endpoint, json=request).status_code == 200
        monkeypatch.setattr(
            app_module, "render_answer", lambda result: alter_volume(real_render(result), label)
        )
        response = client.post(endpoint, json=request)
    assert response.status_code == 500
    assert response.json() == {"detail": "Generated answer failed grounding checks"}
