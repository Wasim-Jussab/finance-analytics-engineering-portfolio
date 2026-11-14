from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from operations_assistant import app as app_module
from operations_assistant.generate import build_snapshot


@pytest.mark.parametrize("endpoint", ["/api/answers", "/api/questions"])
def test_runtime_refuses_numeric_prose_drift_before_returning_answer(
    tmp_path, monkeypatch, endpoint
):
    database = tmp_path / "synthetic.duckdb"
    build_snapshot(database)
    real_render = app_module.render_answer
    request = {"start": "2026-09-21", "end": "2026-09-28"}
    request.update(
        {"name": "delivery_summary"}
        if endpoint == "/api/answers"
        else {"question": "Give me delivery totals for this period"}
    )

    def changed_render(result):
        rendered = deepcopy(real_render(result))
        assert "rate is 70.18%;" in rendered["answer"]
        rendered["answer"] = rendered["answer"].replace("rate is 70.18%;", "rate is 99.99%;")
        return rendered

    with TestClient(app_module.create_app(database)) as client:
        healthy = client.post(endpoint, json=request)
        assert healthy.status_code == 200
        monkeypatch.setattr(app_module, "render_answer", changed_render)
        refused = client.post(endpoint, json=request)
    assert refused.status_code == 500
    assert refused.json() == {"detail": "Generated answer failed grounding checks"}
    assert "claims" not in refused.json()
