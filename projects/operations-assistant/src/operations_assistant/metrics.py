"""The dashboard and later assistant share these parameterised metric queries."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb

from operations_assistant.generate import REGIONS

DEFINITION = (
    "On-time completion rate = shipments delivered by the promised timestamp / "
    "all non-cancelled shipments due in the selected promised-date period. "
    "Late deliveries and overdue open shipments stay in the denominator. "
    "Periods use UTC dates with an inclusive start and exclusive end."
)


def summary(database: Path, start: date, end: date, region: str | None = None) -> dict:
    if start >= end:
        raise ValueError("Start must precede the exclusive end date")
    if region is not None and region not in REGIONS:
        raise ValueError("Unknown region")
    if not database.is_file():
        raise FileNotFoundError("Generate the synthetic snapshot before starting the application")
    with duckdb.connect(str(database), read_only=True) as connection:
        connection.execute("SET TimeZone='UTC'")
        as_of = connection.execute("SELECT as_of FROM snapshot_metadata").fetchone()[0]
        if end > as_of.date():
            raise ValueError("Period must contain complete days within the snapshot")
        rows = connection.execute(
            """
            SELECT shipment_id, region, promised_at, delivered_at, source_status
            FROM shipments
            WHERE promised_at >= CAST(? AS DATE)
              AND promised_at < CAST(? AS DATE)
              AND dispatched_at <= ?
              AND (? IS NULL OR region = ?)
            ORDER BY promised_at, region, shipment_id
        """,
            [start, end, as_of, region, region],
        ).fetchall()

    buckets: dict[str, dict] = {}
    days: dict[str, dict] = {}
    details = []
    totals = {"due": 0, "on_time": 0, "late_delivered": 0, "overdue_open": 0, "cancelled": 0}
    for shipment_id, shipment_region, promised, delivered, source_status in rows:
        outcome = (
            "cancelled"
            if source_status == "Cancelled"
            else "overdue_open"
            if delivered is None
            else "on_time"
            if delivered <= promised
            else "late_delivered"
        )
        for aggregate in (
            totals,
            buckets.setdefault(shipment_region, dict.fromkeys(totals, 0)),
            days.setdefault(promised.date().isoformat(), dict.fromkeys(totals, 0)),
        ):
            aggregate[outcome] += 1
            if outcome != "cancelled":
                aggregate["due"] += 1
        if outcome in ("late_delivered", "overdue_open"):
            details.append(
                {
                    "shipment_id": shipment_id,
                    "region": shipment_region,
                    "promised_at": promised.isoformat(),
                    "outcome": outcome,
                }
            )

    def add_rate(counts: dict) -> dict:
        assert (
            counts["due"] == counts["on_time"] + counts["late_delivered"] + counts["overdue_open"]
        )
        return {
            **counts,
            "on_time_rate": counts["on_time"] / counts["due"] if counts["due"] else None,
        }

    return {
        "period": {"start_inclusive": start.isoformat(), "end_exclusive": end.isoformat()},
        "as_of": as_of.isoformat(),
        "synthetic": True,
        "definition": DEFINITION,
        "selected_region": region,
        "totals": add_rate(totals),
        "regions": [{"region": key, **add_rate(value)} for key, value in sorted(buckets.items())],
        "daily": [{"date": key, **add_rate(value)} for key, value in sorted(days.items())],
        "exceptions": details,
        "evidence": {
            "source": "shipments",
            "grain": "one row per shipment",
            "observed_rows": len(rows),
            "cancelled_rows_excluded": totals["cancelled"],
        },
    }
