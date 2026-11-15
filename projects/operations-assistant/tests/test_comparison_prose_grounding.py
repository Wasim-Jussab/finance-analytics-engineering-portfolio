from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from operations_assistant import app as app_module
from operations_assistant.answers import render_answer
from operations_assistant.evaluation import evaluate_answer
from operations_assistant.generate import build_snapshot
from operations_assistant.tools import ToolRequest, execute_tool


def comparison():
    return {
        "start": "2026-09-21",
        "end": "2026-09-28",
        "baseline_start": "2026-09-14",
        "baseline_end": "2026-09-21",
    }


@pytest.mark.parametrize(
    ("original", "edited", "claim"),
    [
        ("had 213 due", "had 999 due", "baseline"),
        ("at 82.63%;", "at 99.99%;", "baseline"),
        ("had 218 at", "had 999 at", "current"),
        ("at 70.18%.", "at 99.99%.", "current"),
        ("-12.45 percentage points.", "+12.45 percentage points.", "rate change"),
    ],
)
def test_comparison_prose_drift_fails_with_unchanged_evidence(tmp_path, original, edited, claim):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    result = execute_tool(database, ToolRequest(name="compare_delivery_periods", **comparison()))
    answer = render_answer(result)
    assert evaluate_answer(result, answer) == []
    changed = deepcopy(answer)
    assert original in changed["answer"]
    changed["answer"] = changed["answer"].replace(original, edited)
    assert changed["claims"] == answer["claims"]
    assert changed["evidence"] == answer["evidence"]
    assert evaluate_answer(result, changed) == [
        f"comparison prose {claim} does not match the approved tool result"
    ]


@pytest.mark.parametrize("endpoint", ["/api/answers", "/api/questions"])
def test_api_refuses_changed_comparison_rate_direction(tmp_path, monkeypatch, endpoint):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    real_render = app_module.render_answer

    def changed_render(result):
        answer = real_render(result)
        answer["answer"] = answer["answer"].replace(
            "-12.45 percentage points.", "+12.45 percentage points."
        )
        return answer

    request = comparison()
    request.update(
        {"name": "compare_delivery_periods"}
        if endpoint == "/api/answers"
        else {"question": "Compare delivery performance between these periods"}
    )
    with TestClient(app_module.create_app(database)) as client:
        assert client.post(endpoint, json=request).status_code == 200
        monkeypatch.setattr(app_module, "render_answer", changed_render)
        refused = client.post(endpoint, json=request)
    assert refused.status_code == 500
    assert refused.json() == {"detail": "Generated answer failed grounding checks"}
