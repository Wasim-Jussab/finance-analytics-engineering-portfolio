"""Prove key-based incremental inserts, updates and repeatable reruns."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from finance_portfolio.snapshot_scenario import build_selection, temporary_database_copy

LATE_PAYMENT_ID = "SPAY-LATE-0001"
INCREMENTAL_SELECTOR = "fct_subscription_payment+"


def payment_summary(database: Path) -> tuple[int, int, int]:
    """Return row count, distinct keys and collected count from the incremental fact."""
    with duckdb.connect(str(database), read_only=True) as connection:
        return connection.execute(
            """
            SELECT
                COUNT(*),
                COUNT(DISTINCT subscription_payment_id),
                COUNT(*) FILTER (WHERE is_collected)
            FROM mart.fct_subscription_payment
            """
        ).fetchone()


def apply_controlled_changes(database: Path) -> str:
    """Correct one failed attempt and add one late-arriving retry to the raw source."""
    with duckdb.connect(str(database)) as connection:
        corrected_payment_id = connection.execute(
            """
            SELECT subscription_payment_id
            FROM raw.subscription_payments
            WHERE payment_status = 'Failed'
            ORDER BY subscription_payment_id
            LIMIT 1
            """
        ).fetchone()[0]

        connection.execute(
            """
            UPDATE raw.subscription_payments
            SET payment_status = 'Completed'
            WHERE subscription_payment_id = ?
            """,
            [corrected_payment_id],
        )
        connection.execute(
            """
            INSERT INTO raw.subscription_payments (
                subscription_payment_id,
                subscription_id,
                billing_date,
                amount,
                payment_status,
                load_id,
                loaded_at
            )
            SELECT
                ?,
                subscription_id,
                billing_date,
                amount,
                'Failed',
                load_id,
                loaded_at
            FROM raw.subscription_payments
            WHERE subscription_payment_id = ?
            """,
            [LATE_PAYMENT_ID, corrected_payment_id],
        )
        connection.execute("force checkpoint")
    return corrected_payment_id


def assert_controlled_result(
    database: Path,
    corrected_payment_id: str,
    expected_count: int,
    expected_collected_count: int,
) -> None:
    """Check the merge inserted one key and updated the existing key in place."""
    with duckdb.connect(str(database), read_only=True) as connection:
        summary = connection.execute(
            """
            SELECT
                COUNT(*),
                COUNT(DISTINCT subscription_payment_id),
                COUNT(*) FILTER (WHERE is_collected)
            FROM mart.fct_subscription_payment
            """
        ).fetchone()
        corrected = connection.execute(
            """
            SELECT payment_status, is_collected
            FROM mart.fct_subscription_payment
            WHERE subscription_payment_id = ?
            """,
            [corrected_payment_id],
        ).fetchone()
        late_row = connection.execute(
            """
            SELECT payment_status, is_collected
            FROM mart.fct_subscription_payment
            WHERE subscription_payment_id = ?
            """,
            [LATE_PAYMENT_ID],
        ).fetchone()

    assert summary == (expected_count, expected_count, expected_collected_count)
    assert corrected == ("Completed", True)
    assert late_row == ("Failed", False)


def run_check(source_database: Path) -> None:
    """Exercise initial state, no-change rerun, merge changes and idempotent rerun."""
    with temporary_database_copy(source_database, "incremental-payment-") as database:
        baseline = payment_summary(database)
        assert baseline[0] == baseline[1]

        build_selection(database, INCREMENTAL_SELECTOR)
        assert payment_summary(database) == baseline

        corrected_payment_id = apply_controlled_changes(database)
        build_selection(database, INCREMENTAL_SELECTOR)
        assert_controlled_result(
            database,
            corrected_payment_id,
            baseline[0] + 1,
            baseline[2] + 1,
        )

        build_selection(database, INCREMENTAL_SELECTOR)
        assert_controlled_result(
            database,
            corrected_payment_id,
            baseline[0] + 1,
            baseline[2] + 1,
        )

        print(
            "Incremental payment check passed: unchanged input stayed stable, "
            "one late key was inserted, one existing key was updated and the "
            "second rerun remained idempotent."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    run_check(args.database)


if __name__ == "__main__":
    main()
