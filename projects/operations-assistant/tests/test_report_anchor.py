import json
import subprocess
import sys
from pathlib import Path

import pytest
from operations_assistant.evidence import investigation_digest
from operations_assistant.generate import build_snapshot
from operations_assistant.investigation import collect_exceptions
from operations_assistant.investigation_verify import verify_investigation
from operations_assistant.tools import ToolRequest


def build_report(tmp_path: Path, empty: bool = False):
    db = tmp_path / "operations.duckdb"
    build_snapshot(db)
    return collect_exceptions(
        db,
        ToolRequest.model_validate(
            {
                "name": "delivery_exceptions",
                "start": "2026-09-01" if empty else "2026-09-21",
                "end": "2026-09-02" if empty else "2026-09-28",
                "limit": 7,
                "outcome": "overdue_open",
            }
        ),
    )


@pytest.mark.parametrize("empty", [False, True])
def test_canonical_report_roundtrip_and_external_anchor(tmp_path: Path, empty):
    report = build_report(tmp_path, empty)
    retained = report["report_sha256"]
    saved = json.loads(json.dumps(report, indent=3, sort_keys=False))
    assert investigation_digest(saved) == retained
    verified = verify_investigation(saved, expected_report_sha256=retained)
    assert verified["embedded_report_digest_checked"] is True
    assert verified["external_report_anchor_checked"] is True
    assert verified["database_opened"] is False


def test_consistent_rewrite_requires_independent_anchor_to_detect(tmp_path: Path):
    report = build_report(tmp_path)
    retained = report["report_sha256"]
    report["max_rows"] = 999
    report["report_sha256"] = investigation_digest(report)
    unanchored = verify_investigation(report)
    assert unanchored["external_report_anchor_checked"] is False
    with pytest.raises(ValueError, match="externally retained digest"):
        verify_investigation(report, expected_report_sha256=retained)


def test_embedded_digest_detects_unrehashed_edits(tmp_path: Path):
    report = build_report(tmp_path)
    report["max_rows"] = 999
    with pytest.raises(ValueError, match="Whole-report digest"):
        verify_investigation(report)


@pytest.mark.parametrize("digest", ["bad", "G" * 64])
def test_malformed_external_digest_is_rejected(tmp_path: Path, digest):
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        verify_investigation(build_report(tmp_path), expected_report_sha256=digest)


def test_legacy_v1_remains_structurally_verifiable_without_embedded_digest(tmp_path: Path):
    report = build_report(tmp_path)
    report["contract_version"] = "investigation-v1"
    report.pop("report_sha256")
    verified = verify_investigation(report)
    assert verified["integrity"] == "verified"
    assert verified["embedded_report_digest_checked"] is False
    assert verified["external_report_anchor_checked"] is False


def test_external_anchor_cli_rejects_rehashed_replacement(tmp_path: Path):
    report = build_report(tmp_path)
    retained = report["report_sha256"]
    path = tmp_path / "investigation.json"
    path.write_text(json.dumps(report))
    command = [
        sys.executable,
        "-m",
        "operations_assistant.investigation_verify",
        str(path),
        "--expected-report-sha256",
        retained,
    ]
    success = subprocess.run(command, capture_output=True, text=True, check=False)
    assert success.returncode == 0
    assert json.loads(success.stdout)["external_report_anchor_checked"] is True
    report["max_rows"] = 999
    report["report_sha256"] = investigation_digest(report)
    path.write_text(json.dumps(report))
    failed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert failed.returncode == 1
    assert failed.stdout == ""


def test_nonfinite_report_values_cannot_be_hashed(tmp_path: Path):
    report = build_report(tmp_path)
    report["max_rows"] = float("nan")
    with pytest.raises(ValueError):
        investigation_digest(report)
