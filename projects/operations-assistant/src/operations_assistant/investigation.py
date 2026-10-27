"""Bounded deterministic orchestration of the existing approved exception tool."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from operations_assistant.tools import ToolRequest, execute_tool


def collect_exceptions(database: Path, request: ToolRequest, max_rows: int = 1000) -> dict:
    """Collect a complete, snapshot-pinned result or raise without returning a partial set."""
    if request.name != "delivery_exceptions" or request.offset not in (None, 0):
        raise ValueError("Investigation requires exception detail starting at offset zero")
    if not 1 <= max_rows <= 1000:
        raise ValueError("Investigation row cap must be between 1 and 1000")
    rows: list[dict] = []
    pages: list[dict] = []
    snapshot_id = request.expected_snapshot_id
    total = None
    offset = 0
    while True:
        page_request = ToolRequest.model_validate(
            {**request.model_dump(), "offset": offset, "expected_snapshot_id": snapshot_id}
        )
        page = execute_tool(database, page_request)
        observed_snapshot = page["evidence"]["snapshot_id"]
        if snapshot_id is not None and observed_snapshot != snapshot_id:
            raise ValueError("Investigation snapshot identity changed")
        snapshot_id = observed_snapshot
        if total is None:
            total = page["exception_count"]
            if total > max_rows:
                raise ValueError("Exception population exceeds the investigation row cap")
        if page["exception_count"] != total or page["offset"] != offset:
            raise ValueError("Investigation population or offset changed")
        if page["returned_count"] != len(page["rows"]):
            raise ValueError("Investigation page count does not reconcile")
        rows.extend(page["rows"])
        if len(rows) > total or len(rows) > max_rows:
            raise ValueError("Investigation returned more rows than expected")
        pages.append(page["evidence"])
        if not page["has_more"]:
            if page["next_offset"] is not None or len(rows) != total:
                raise ValueError("Investigation ended before its population reconciled")
            break
        next_offset = page["next_offset"]
        if next_offset != offset + len(page["rows"]) or next_offset <= offset:
            raise ValueError("Investigation pagination did not advance consistently")
        offset = next_offset
    if len({row["shipment_id"] for row in rows}) != total:
        raise ValueError("Investigation contains duplicate shipment IDs")
    return {
        "mode": "deterministic read-only investigation; no model inference",
        "request": request.model_dump(mode="json"),
        "max_rows": max_rows,
        "snapshot_id": snapshot_id,
        "exception_count": total,
        "rows": rows,
        "page_evidence": pages,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/operations.duckdb"))
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    parser.add_argument("--outcome", choices=["late_delivered", "overdue_open"])
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--max-rows", type=int, default=1000)
    args = parser.parse_args()
    request = ToolRequest(
        name="delivery_exceptions",
        start=args.start,
        end=args.end,
        outcome=args.outcome,
        limit=args.limit,
    )
    print(json.dumps(collect_exceptions(args.database, request, args.max_rows), indent=2))


if __name__ == "__main__":
    main()
