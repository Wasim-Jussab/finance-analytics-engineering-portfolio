from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from operations_assistant import app as app_module
from operations_assistant.answers import render_answer
from operations_assistant.evaluation import evaluate_answer
from operations_assistant.generate import build_snapshot
from operations_assistant.tools import ToolRequest, execute_tool

PARAMETERS = dict(start='2026-09-21', end='2026-09-28')
MUTATIONS = [('2026-09-21', '2026-09-20'), ('2026-09-28', '2026-09-29'),
             ('(exclusive end)', '(inclusive end)')]


def drift(answer, before, after):
    changed = deepcopy(answer)
    changed['answer'] = changed['answer'].replace(before, after, 1)
    assert changed['answer'] != answer['answer']
    return changed


@pytest.mark.parametrize(('before', 'after'), MUTATIONS)
def test_summary_window_cannot_drift_with_unchanged_claims(tmp_path, before, after):
    database = tmp_path / 'synthetic.duckdb'
    build_snapshot(database)
    result = execute_tool(database, ToolRequest(name='delivery_summary', **PARAMETERS))
    answer = render_answer(result)
    assert evaluate_answer(result, answer) == []
    changed = drift(answer, before, after)
    assert changed['claims'] == answer['claims']
    assert changed['evidence'] == answer['evidence']
    assert 'summary prose period does not match the approved tool result' in (
        evaluate_answer(result, changed)
    )


@pytest.mark.parametrize(('before', 'after'), MUTATIONS)
@pytest.mark.parametrize('endpoint', ['/api/answers', '/api/questions'])
def test_api_refuses_wrong_summary_window(tmp_path, monkeypatch, before, after, endpoint):
    database = tmp_path / 'synthetic.duckdb'
    build_snapshot(database)
    real_render = app_module.render_answer
    request = dict(PARAMETERS)
    request.update(
        {'name': 'delivery_summary'} if endpoint == '/api/answers'
        else {'question': 'Give me delivery totals for this period'}
    )
    with TestClient(app_module.create_app(database)) as client:
        assert client.post(endpoint, json=request).status_code == 200
        monkeypatch.setattr(
            app_module, 'render_answer', lambda result: drift(real_render(result), before, after)
        )
        response = client.post(endpoint, json=request)
    assert response.status_code == 500
    assert response.json() == {'detail': 'Generated answer failed grounding checks'}
