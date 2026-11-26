"""Bounded read-only review of synthetic ranked shortfall movements."""

from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb


def build_review(database: Path, snapshot_date: date, direction: str, limit: int = 5) -> dict:
    if direction not in {"Increase", "Decrease"}:
        raise ValueError("Direction must be Increase or Decrease")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
        raise ValueError("Limit must be an integer from 1 to 50")
    if type(snapshot_date) is not date:
        raise ValueError("Snapshot date must be a date")
    with duckdb.connect(str(database), read_only=True) as con:
        con.begin()
        observed, comparable = con.execute(
            "select count(*), bool_or(has_previous_month) "
            "from mart.rpt_loan_shortfall_change_ranked where snapshot_date = ?",
            [snapshot_date],
        ).fetchone()
        if not observed:
            raise ValueError("Snapshot date is not available")
        if not comparable:
            raise ValueError("Comparison month is not available")
        summaries = con.execute(
            "select contributing_account_count, direction_gross_change_amount "
            "from mart.agg_loan_shortfall_concentration "
            "where snapshot_date = ? and change_direction = ?",
            [snapshot_date, direction],
        ).fetchall()
        if len(summaries) > 1:
            raise ValueError("Direction summary does not reconcile: duplicate grain")
        summary = summaries[0] if summaries else None
        count, gross, first_rank, last_rank, distinct_ranks, accounts, signs = con.execute(
            "select count(*), sum(abs(scheduled_principal_shortfall_change)), "
            "min(direction_rank), max(direction_rank), count(distinct direction_rank), "
            "count(distinct account_id), sum(sign(scheduled_principal_shortfall_change)) "
            "from mart.rpt_loan_shortfall_change_ranked "
            "where snapshot_date = ? and change_direction = ?",
            [snapshot_date, direction],
        ).fetchone()
        if summary is None and count:
            raise ValueError("Direction summary does not reconcile: missing direction")
        if summary is not None and (
            count <= 0
            or gross is None
            or gross <= 0
            or summary != (count, gross)
            or (first_rank, last_rank, distinct_ranks) != (1, count, count)
            or accounts != count
            or signs != (count if direction == "Increase" else -count)
        ):
            raise ValueError("Direction summary does not reconcile to full ranked population")
        rows = con.execute(
            "select account_id, direction_rank, scheduled_principal_shortfall_change "
            "from mart.rpt_loan_shortfall_change_ranked "
            "where snapshot_date = ? and change_direction = ? and direction_rank <= ? "
            "order by direction_rank",
            [snapshot_date, direction, limit],
        ).fetchall()
        con.commit()
    if summary and summary[1] <= 0:
        raise ValueError("Direction gross amount must be positive")
    selected = sum((abs(row[2]) for row in rows), Decimal("0.00"))
    return {
        "mode": "synthetic principal-position movement; deterministic read-only review",
        "snapshot_date": snapshot_date.isoformat(),
        "direction": direction,
        "limit": limit,
        "status": "available" if summary else "direction_absent",
        "contributing_accounts": summary[0] if summary else None,
        "direction_gross_change_amount": str(summary[1]) if summary else None,
        "returned_accounts": len(rows),
        "selected_gross_change_amount": str(selected) if summary else None,
        "selected_gross_change_share": float(selected / summary[1]) if summary else None,
        "has_more": len(rows) < summary[0] if summary else False,
        "rows": [
            {
                "account_id": row[0],
                "direction_rank": row[1],
                "signed_shortfall_change_amount": str(row[2]),
            }
            for row in rows
        ],
        "limitation": (
            "Gross direction denominator is not truncated. Not cash flow or treatment policy."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/finance.duckdb"))
    parser.add_argument("--snapshot-date", type=date.fromisoformat, required=True)
    parser.add_argument("--direction", choices=["Increase", "Decrease"], required=True)
    parser.add_argument("--limit", type=int, default=5)
    arguments = parser.parse_args()
    try:
        review = build_review(
            arguments.database, arguments.snapshot_date, arguments.direction, arguments.limit
        )
    except (ValueError, duckdb.Error) as error:
        parser.exit(2, f"Review unavailable: {error}\n")
    print(json.dumps(review, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
