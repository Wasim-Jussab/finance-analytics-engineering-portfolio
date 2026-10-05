"""Generate a deterministic, explicitly synthetic delivery snapshot."""

from __future__ import annotations

import argparse
import os
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import duckdb

AS_OF = datetime(2026, 9, 28, tzinfo=UTC)
REGIONS = ("London", "Midlands", "North", "South")


def generate_rows(seed: int = 42) -> list[tuple]:
    rng = random.Random(seed)
    rows = []
    for day in range(14):
        for number in range(32):
            region = REGIONS[number % len(REGIONS)]
            promised = datetime(2026, 9, 14, 17, tzinfo=UTC) + timedelta(days=day)
            dispatched = promised - timedelta(days=2, hours=3)
            outcome = rng.random()
            # An invented regional shift creates a useful comparison, not causal evidence.
            late_threshold = 0.50 if day >= 7 and region == "Midlands" else 0.18
            if outcome < 0.06:
                status, delivered = "Cancelled", None
            elif outcome < late_threshold:
                delivered = promised + timedelta(hours=rng.choice((6, 12, 24, 36)))
                status = "Delivered" if delivered <= AS_OF else "In Transit"
                delivered = delivered if status == "Delivered" else None
            elif outcome > 0.94:
                status, delivered = "In Transit", None
            else:
                status = "Delivered"
                delivered = promised - timedelta(hours=rng.choice((0, 2, 6, 12)))
            rows.append(
                (f"SHP-{day:02d}-{number:03d}", region, dispatched, promised, delivered, status)
            )
    return rows


def validate_rows(rows: list[tuple], as_of: datetime = AS_OF) -> None:
    keys = [row[0] for row in rows]
    if not rows or len(keys) != len(set(keys)):
        raise ValueError("Snapshot must be nonempty with unique shipment IDs")
    for key, region, dispatched, promised, delivered, status in rows:
        if region not in REGIONS or status not in ("Delivered", "In Transit", "Cancelled"):
            raise ValueError(f"Invalid region or status: {key}")
        dates = [dispatched, promised, *([delivered] if delivered is not None else [])]
        if any(d.tzinfo is None for d in dates):
            raise ValueError(f"Timestamps must be timezone-aware: {key}")
        if dispatched > promised or dispatched > as_of:
            raise ValueError(f"Invalid dispatch chronology: {key}")
        if (status == "Delivered") != (delivered is not None):
            raise ValueError(f"Status and delivery timestamp disagree: {key}")
        if delivered is not None and not dispatched <= delivered <= as_of:
            raise ValueError(f"Invalid delivery chronology: {key}")


def build_snapshot(path: Path, rows: list[tuple] | None = None) -> int:
    records = generate_rows() if rows is None else rows
    validate_rows(records)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.stem}-{uuid4()}.duckdb")
    try:
        with duckdb.connect(str(temporary)) as connection:
            connection.execute("SET TimeZone='UTC'")
            connection.execute("""
                CREATE TABLE shipments (
                    shipment_id VARCHAR PRIMARY KEY, region VARCHAR NOT NULL,
                    dispatched_at TIMESTAMPTZ NOT NULL, promised_at TIMESTAMPTZ NOT NULL,
                    delivered_at TIMESTAMPTZ, source_status VARCHAR NOT NULL
                );
                CREATE TABLE snapshot_metadata (as_of TIMESTAMPTZ NOT NULL, seed INTEGER);
            """)
            connection.executemany("INSERT INTO shipments VALUES (?, ?, ?, ?, ?, ?)", records)
            connection.execute(
                "INSERT INTO snapshot_metadata VALUES (?, ?)",
                [AS_OF, 42 if rows is None else None],
            )
            connection.execute("CHECKPOINT")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/operations.duckdb"))
    args = parser.parse_args()
    print(
        f"Generated {build_snapshot(args.database)} synthetic shipments; as of {AS_OF.isoformat()}"
    )


if __name__ == "__main__":
    main()
