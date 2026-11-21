from copy import deepcopy

import pytest
from fastapi.testclient import TestClient
from operations_assistant import app as app_module
from operations_assistant.answers import render_answer
from operations_assistant.evaluation import evaluate_answer
from operations_assistant.generate import build_snapshot
from operations_assistant.tools import ToolRequest, execute_tool

PERIODS = [('2026-09-21', '2026-09-28'), ('2026-08-31', '2026-09-07')]
REPLACEMENTS = ['the numerator', "a different period's denominator"]


def drift(answer, replacement):
    changed = deepcopy(answer)
    changed['answer'] = changed['answer'].replace('that denominator', replacement, 1)
    assert changed['answer'] != answer['answer']
    return changed


@pytest.mark.parametrize(('start', 'end'), PERIODS)
@pytest.mark.parametrize('replacement', REPLACEMENTS)
def test_denominator_sentence_must_match_with_unchanged_numbers(tmp_path, start, end, replacement):
    database = tmp_path / 'synthetic.duckdb'
    build_snapshot(database)
    result = execute_tool(database, ToolRequest(name='delivery_summary', start=start, end=end))
    answer = render_answer(result)
    assert (answer['claims']['on_time_rate'] is None) == (start == '2026-08-31')
    assert evaluate_answer(result, answer) == []
    changed = drift(answer, replacement)
    assert changed['claims'] == answer['claims']
    assert changed['evidence'] == answer['evidence']
    assert 'summary prose cancelled does not match the approved tool result' in (
        evaluate_answer(result, changed)
    )


@pytest.mark.parametrize(('start', 'end'), PERIODS)
@pytest.mark.parametrize('replacement', REPLACEMENTS)
@pytest.mark.parametrize('endpoint', ['/api/answers', '/api/questions'])
def test_api_refuses_wrong_denominator_sentence(
    tmp_path, monkeypatch, start, end, replacement, endpoint
):
    database = tmp_path / 'synthetic.duckdb'
    build_snapshot(database)
    real_render = app_module.render_answer
    request = dict(start=start, end=end)
    request.update(
        {'name': 'delivery_summary'} if endpoint == '/api/answers'
        else {'question': 'Give me delivery totals for this period'}
    )
    with TestClient(app_module.create_app(database)) as client:
        assert client.post(endpoint, json=request).status_code == 200
        monkeypatch.setattr(
            app_module, 'render_answer', lambda result: drift(real_render(result), replacement)
        )
        response = client.post(endpoint, json=request)
    assert response.status_code == 500
    assert response.json() == {'detail': 'Generated answer failed grounding checks'}
