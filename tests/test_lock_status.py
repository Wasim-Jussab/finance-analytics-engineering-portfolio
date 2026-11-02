import json

import pytest

from finance_portfolio.lock_status import inspect_lock

RUN = "12345678-1234-1234-1234-123456789abc"


def fixture(tmp_path, status="succeeded"):
    lock = tmp_path / "pipeline.lock"
    lock.write_text(json.dumps({"run_id": RUN, "process_id": 42, "started_at": "start"}))
    evidence = tmp_path / f"{RUN}.json"
    evidence.write_text(
        json.dumps(
            {"run_id": RUN, "started_at": "start", "finished_at": "finish", "status": status}
        )
    )
    return lock, evidence


@pytest.mark.parametrize("status", ["succeeded", "failed"])
def test_completed_evidence_does_not_authorise_removal(tmp_path, status):
    lock, evidence = fixture(tmp_path, status)
    before = lock.read_bytes(), evidence.read_bytes()
    result = inspect_lock(lock, tmp_path)
    assert result["status"] == "retained_completed_run"
    assert result["matching_run_status"] == status
    assert result["safe_to_remove"] is False
    assert before == (lock.read_bytes(), evidence.read_bytes())


def test_missing_lock_is_not_created(tmp_path):
    lock = tmp_path / "missing"
    assert inspect_lock(lock, tmp_path)["status"] == "unlocked"
    assert not lock.exists()


@pytest.mark.parametrize(
    "payload", ["invalid", "[]", '{"run_id":"../../secret"}', '{"run_id":1,"process_id":true}']
)
def test_malformed_metadata_is_unresolved_and_sanitised(tmp_path, payload):
    lock = tmp_path / "private.lock"
    lock.write_text(payload)
    result = inspect_lock(lock, tmp_path)
    assert result["status"] == "unresolved"
    assert str(tmp_path) not in json.dumps(result)
    assert lock.read_text() == payload


@pytest.mark.parametrize(
    "field,value",
    [("run_id", "other"), ("started_at", "other"), ("status", "running"), ("finished_at", None)],
)
def test_mismatched_or_incomplete_evidence_is_not_completion(tmp_path, field, value):
    lock, evidence = fixture(tmp_path)
    report = json.loads(evidence.read_text())
    evidence.write_text(json.dumps({**report, field: value}))
    assert inspect_lock(lock, tmp_path)["status"] == "unresolved"


def test_missing_report_is_unresolved(tmp_path):
    lock, evidence = fixture(tmp_path)
    evidence.unlink()
    assert inspect_lock(lock, tmp_path)["status"] == "unresolved"
