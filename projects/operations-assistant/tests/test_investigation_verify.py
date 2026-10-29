import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest
from operations_assistant.evidence import evidence_digest, investigation_digest
from operations_assistant.generate import build_snapshot
from operations_assistant.investigation import collect_exceptions
from operations_assistant.investigation_verify import verify_investigation
from operations_assistant.tools import ToolRequest


def report(database: Path, **kwargs):
    return collect_exceptions(
        database,
        ToolRequest.model_validate(
            {
                "name": "delivery_exceptions",
                "start": "2026-09-21",
                "end": "2026-09-28",
                "outcome": "overdue_open",
                "limit": 7,
                **kwargs,
            }
        ),
    )


@pytest.mark.parametrize("empty", [False, True])
def test_json_roundtrip_verifies_without_opening_database(tmp_path: Path, monkeypatch, empty):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    result = report(db, **({"start": "2026-09-01", "end": "2026-09-02"} if empty else {}))
    saved = json.loads(json.dumps(result))

    def no_connection(*args, **kwargs):
        raise AssertionError("Offline verification must not open DuckDB")

    monkeypatch.setattr(duckdb, "connect", no_connection)
    verified = verify_investigation(saved, expected_snapshot_id=result["snapshot_id"])
    assert verified["integrity"] == "verified"
    assert verified["rows"] == (0 if empty else 21)
    assert verified["database_opened"] is False
    with pytest.raises(ValueError, match="expected snapshot"):
        verify_investigation(saved, expected_snapshot_id="0" * 64)


@pytest.mark.parametrize(
    "fault", ["digest", "rows", "request", "count", "pages", "pin", "mode", "provenance"]
)
def test_tampered_or_incomplete_report_is_rejected(tmp_path: Path, fault):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    saved = copy.deepcopy(report(db))
    if fault == "digest":
        saved["pages"][0]["rows"][0]["shipment_id"] = "changed"
    elif fault == "rows":
        saved["rows"] = saved["rows"][:-1]
    elif fault == "request":
        saved["request"]["region"] = "North"
    elif fault == "count":
        saved["exception_count"] += 1
    elif fault == "pages":
        saved["pages"].pop()
    elif fault == "mode":
        saved["mode"] = "generative AI"
    elif fault == "provenance":
        saved["pages"][0]["evidence"]["source"] = "unknown"
    elif fault == "pin":
        page = saved["pages"][1]
        evidence = page["evidence"]
        evidence["request"]["expected_snapshot_id"] = None
        evidence["evidence_id"] = evidence_digest(
            evidence["snapshot_id"],
            evidence["request"],
            {k: v for k, v in page.items() if k != "evidence"},
            "delivery-v1",
        )
    saved["report_sha256"] = investigation_digest(saved)
    with pytest.raises(ValueError):
        verify_investigation(saved)


def test_evidence_digest_preserves_existing_tool_contract(tmp_path: Path):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    page = report(db)["pages"][0]
    evidence = page["evidence"]
    old_payload = {
        "snapshot_id": evidence["snapshot_id"],
        "request": evidence["request"],
        "result": {k: v for k, v in page.items() if k != "evidence"},
        "contract_version": "delivery-v1",
    }
    assert (
        evidence["evidence_id"]
        == hashlib.sha256(json.dumps(old_payload, sort_keys=True, default=str).encode()).hexdigest()
    )


def test_offline_verification_cli_success_and_rejection(tmp_path: Path):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    saved = report(db)
    path = tmp_path / "investigation.json"
    path.write_text(json.dumps(saved))
    command = [sys.executable, "-m", "operations_assistant.investigation_verify", str(path)]
    success = subprocess.run(command, capture_output=True, text=True, check=False)
    assert success.returncode == 0
    assert json.loads(success.stdout)["rows"] == 21
    saved["rows"] = []
    path.write_text(json.dumps(saved))
    rejected = subprocess.run(command, capture_output=True, text=True, check=False)
    assert rejected.returncode == 1
    assert rejected.stdout == ""
    assert "verification failed" in rejected.stderr
