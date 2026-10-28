"""Verify saved investigation integrity offline without opening a database."""

import argparse
import json
from pathlib import Path

from operations_assistant.evidence import evidence_digest
from operations_assistant.tools import ToolRequest


def verify_investigation(report: dict, expected_snapshot_id: str | None = None) -> dict:
    try:
        if report["contract_version"] != "investigation-v1":
            raise ValueError("Unsupported investigation contract")
        if report["mode"] != "deterministic read-only investigation; no model inference":
            raise ValueError("Unsupported investigation mode")
        request = ToolRequest.model_validate(report["request"])
        if request.name != "delivery_exceptions" or request.offset not in (None, 0):
            raise ValueError("Invalid investigation starting request")
        snapshot_id = report["snapshot_id"]
        ToolRequest.model_validate({**request.model_dump(), "expected_snapshot_id": snapshot_id})
        if expected_snapshot_id is not None and snapshot_id != expected_snapshot_id:
            raise ValueError("Investigation does not match the expected snapshot")
        if request.expected_snapshot_id not in (None, snapshot_id):
            raise ValueError("Initial snapshot expectation does not match")
        total = report["exception_count"]
        cap = report["max_rows"]
        if (
            type(total) is not int
            or type(cap) is not int
            or not 0 <= total <= cap <= 1000
            or cap < 1
        ):
            raise ValueError("Investigation count or cap is invalid")
        pages = report["pages"]
        if not pages or len(pages) != len(report["page_evidence"]):
            raise ValueError("Investigation pages are missing")
        rows = []
        offset = 0
        for index, page in enumerate(pages):
            evidence = page["evidence"]
            if evidence != report["page_evidence"][index]:
                raise ValueError("Page evidence references differ")
            expected = request.model_dump(mode="json")
            expected.update(
                offset=offset,
                expected_snapshot_id=(request.expected_snapshot_id if index == 0 else snapshot_id),
            )
            if evidence["request"] != expected or evidence["snapshot_id"] != snapshot_id:
                raise ValueError("Page request scope or snapshot does not match")
            if evidence["contract_version"] != "delivery-v1":
                raise ValueError("Unsupported tool evidence contract")
            if (
                evidence["source"] != "shipments"
                or evidence["grain"] != "one row per shipment"
                or evidence["mode"] != "deterministic metric computation"
            ):
                raise ValueError("Tool evidence provenance metadata does not match")
            result = {key: value for key, value in page.items() if key != "evidence"}
            if (
                page["tool"] != "delivery_exceptions"
                or page["mode"] != "deterministic"
                or page["period"]
                != {
                    "start_inclusive": request.start.isoformat(),
                    "end_exclusive": request.end.isoformat(),
                }
                or page["selected_region"] != request.region
                or page["selected_outcome"] != request.outcome
                or page["limit"] != (request.limit or 25)
            ):
                raise ValueError("Page result scope does not match the investigation")
            if evidence["evidence_id"] != evidence_digest(
                snapshot_id, expected, result, "delivery-v1"
            ):
                raise ValueError("Page evidence digest does not match")
            if page["exception_count"] != total or page["offset"] != offset:
                raise ValueError("Page population or offset does not reconcile")
            if (
                page["returned_count"] != len(page["rows"])
                or not 0 <= page["returned_count"] <= page["limit"]
            ):
                raise ValueError("Page row count does not reconcile")
            rows.extend(page["rows"])
            offset += len(page["rows"])
            last = index == len(pages) - 1
            if last:
                if page["has_more"] or page["next_offset"] is not None:
                    raise ValueError("Investigation is incomplete")
            elif not page["has_more"] or page["next_offset"] != offset or not page["rows"]:
                raise ValueError("Investigation page sequence does not reconcile")
        if rows != report["rows"] or len(rows) != total:
            raise ValueError("Investigation rows do not reconcile")
        if len({row["shipment_id"] for row in rows}) != total:
            raise ValueError("Investigation contains duplicate shipments")
        return {
            "integrity": "verified",
            "snapshot_id": snapshot_id,
            "rows": total,
            "pages": len(pages),
            "database_opened": False,
            "limitation": "Integrity is not authenticity or business-rule correctness",
        }
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError("Malformed investigation report") from error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--expected-snapshot-id")
    args = parser.parse_args()
    try:
        result = verify_investigation(
            json.loads(args.report.read_text()), args.expected_snapshot_id
        )
    except (ValueError, OSError) as error:
        parser.exit(1, f"Investigation verification failed: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
