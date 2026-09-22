"""Prove incremental inserts, updates, source absence and repeatable reruns."""

from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path

import duckdb

from finance_portfolio.snapshot_scenario import build_selection, temporary_database_copy

LATE_PAYMENT_ID = "SPAY-LATE-0001"
INCREMENTAL_SELECTOR = "fct_subscription_payment+"


def payment_summary(database: Path) -> tuple[int, int, int, int, int]:
    """Return physical, distinct, present, collected-present and absent counts."""
    with duckdb.connect(str(database), read_only=True) as connection:
        return connection.execute(
            """
            SELECT
                COUNT(*),
                COUNT(DISTINCT subscription_payment_id),
                COUNT(*) FILTER (WHERE is_source_present),
                COUNT(*) FILTER (WHERE is_collected AND is_source_present),
                COUNT(*) FILTER (WHERE NOT is_source_present)
            FROM mart.fct_subscription_payment
            """
        ).fetchone()


def health_summary(database: Path) -> tuple[int, int, int, int, int, int, bool]:
    """Return the latest recorded transformation-run metrics."""
    with duckdb.connect(str(database), read_only=True) as connection:
        return connection.execute(
            """
            SELECT
                raw_payment_count,
                physical_fact_count,
                current_fact_count,
                retained_absent_count,
                raw_collected_count,
                current_fact_collected_count,
                is_reconciled
            FROM audit.audit_subscription_payment_run
            ORDER BY observed_at DESC
            LIMIT 1
            """
        ).fetchone()


def health_run_count(database: Path) -> int:
    """Return the number of retained transformation-run audit records."""
    with duckdb.connect(str(database), read_only=True) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM audit.audit_subscription_payment_run"
        ).fetchone()[0]


def run_delta_summary(database: Path) -> tuple[bool, int, int, int, int, int, Decimal]:
    """Read the most recent run's changes against the preceding recorded run."""
    with duckdb.connect(str(database), read_only=True) as connection:
        return connection.execute(
            """
            SELECT
                previous_run_id IS NOT NULL,
                raw_payment_delta,
                physical_fact_delta,
                current_fact_delta,
                retained_absent_delta,
                collected_count_delta,
                collected_amount_delta
            FROM audit.subscription_payment_run_delta
            ORDER BY observed_at DESC, model_run_id DESC
            LIMIT 1
            """
        ).fetchone()


def assert_run_delta(
    database: Path,
    raw: int,
    physical: int,
    current: int,
    absent: int,
    collected: int,
    amount: Decimal,
) -> None:
    """Require the last run to have exactly the expected net changes."""
    assert run_delta_summary(database) == (
        True,
        raw,
        physical,
        current,
        absent,
        collected,
        amount,
    )


def payment_amount(database: Path, payment_id: str) -> Decimal:
    """Read the controlled payment amount from the synthetic source."""
    with duckdb.connect(str(database), read_only=True) as connection:
        return connection.execute(
            """SELECT amount FROM raw.subscription_payments
               WHERE subscription_payment_id = ?""",
            [payment_id],
        ).fetchone()[0]


def assert_health(
    database: Path,
    *,
    raw_count: int,
    physical_count: int,
    current_count: int,
    absent_count: int,
    collected_count: int,
) -> None:
    """Require the latest audit row to describe the expected reconciled state."""
    assert health_summary(database) == (
        raw_count,
        physical_count,
        current_count,
        absent_count,
        collected_count,
        collected_count,
        True,
    )


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
                COUNT(*) FILTER (WHERE is_source_present),
                COUNT(*) FILTER (WHERE is_collected AND is_source_present),
                COUNT(*) FILTER (WHERE NOT is_source_present)
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

    assert summary == (
        expected_count,
        expected_count,
        expected_count,
        expected_collected_count,
        0,
    )
    assert corrected == ("Completed", True)
    assert late_row == ("Failed", False)


def remove_completed_payment(database: Path) -> tuple[object, ...]:
    """Remove one current completed row and return its source values for restoration."""
    with duckdb.connect(str(database)) as connection:
        row = connection.execute(
            """
            SELECT
                subscription_payment_id,
                subscription_id,
                billing_date,
                amount,
                payment_status,
                load_id,
                loaded_at
            FROM raw.subscription_payments
            WHERE payment_status = 'Completed'
            ORDER BY subscription_payment_id
            LIMIT 1
            """
        ).fetchone()
        assert row is not None
        connection.execute(
            "DELETE FROM raw.subscription_payments WHERE subscription_payment_id = ?",
            [row[0]],
        )
        connection.execute("force checkpoint")
    return row


def restore_payment(database: Path, payment: tuple[object, ...]) -> None:
    """Restore the removed source row to prove that presence can be reversed."""
    with duckdb.connect(str(database)) as connection:
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
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            payment,
        )
        connection.execute("force checkpoint")


def assert_absent_payment(
    database: Path,
    payment_id: str,
    expected_physical_count: int,
    expected_present_count: int,
    expected_collected_count: int,
) -> None:
    """Require a missing source key to remain once and leave current metrics."""
    with duckdb.connect(str(database), read_only=True) as connection:
        summary = payment_summary(database)
        presence = connection.execute(
            """
            SELECT is_source_present, source_missing_since
            FROM mart.fct_subscription_payment
            WHERE subscription_payment_id = ?
            """,
            [payment_id],
        ).fetchone()
        monthly_attempts = connection.execute(
            "SELECT SUM(payment_attempt_count) FROM mart.agg_subscription_monthly"
        ).fetchone()[0]

    assert summary == (
        expected_physical_count,
        expected_physical_count,
        expected_present_count,
        expected_collected_count,
        1,
    )
    assert presence[0] is False and presence[1] is not None
    assert monthly_attempts == expected_present_count


def run_check(source_database: Path) -> None:
    """Exercise initial state, no-change rerun, merge changes and idempotent rerun."""
    with temporary_database_copy(source_database, "incremental-payment-") as database:
        baseline = payment_summary(database)
        baseline_health_runs = health_run_count(database)
        with duckdb.connect(str(database), read_only=True) as connection:
            assert connection.execute(
                """SELECT COUNT(*) FROM audit.subscription_payment_run_delta
                   WHERE previous_run_id IS NULL"""
            ).fetchone()[0] == 1
        assert baseline[0] == baseline[1]
        assert baseline[0] == baseline[2]
        assert baseline[4] == 0

        build_selection(database, INCREMENTAL_SELECTOR)
        assert payment_summary(database) == baseline
        assert_health(
            database,
            raw_count=baseline[0],
            physical_count=baseline[0],
            current_count=baseline[0],
            absent_count=0,
            collected_count=baseline[3],
        )
        assert_run_delta(database, 0, 0, 0, 0, 0, Decimal(0))

        corrected_payment_id = apply_controlled_changes(database)
        corrected_amount = payment_amount(database, corrected_payment_id)
        build_selection(database, INCREMENTAL_SELECTOR)
        assert_controlled_result(
            database,
            corrected_payment_id,
            baseline[0] + 1,
            baseline[3] + 1,
        )
        assert_health(
            database,
            raw_count=baseline[0] + 1,
            physical_count=baseline[0] + 1,
            current_count=baseline[0] + 1,
            absent_count=0,
            collected_count=baseline[3] + 1,
        )
        assert_run_delta(database, 1, 1, 1, 0, 1, corrected_amount)

        build_selection(database, INCREMENTAL_SELECTOR)
        assert_controlled_result(
            database,
            corrected_payment_id,
            baseline[0] + 1,
            baseline[3] + 1,
        )
        assert_health(
            database,
            raw_count=baseline[0] + 1,
            physical_count=baseline[0] + 1,
            current_count=baseline[0] + 1,
            absent_count=0,
            collected_count=baseline[3] + 1,
        )
        assert_run_delta(database, 0, 0, 0, 0, 0, Decimal(0))

        removed_payment = remove_completed_payment(database)
        build_selection(database, INCREMENTAL_SELECTOR)
        assert_absent_payment(
            database,
            str(removed_payment[0]),
            baseline[0] + 1,
            baseline[0],
            baseline[3],
        )
        assert_health(
            database,
            raw_count=baseline[0],
            physical_count=baseline[0] + 1,
            current_count=baseline[0],
            absent_count=1,
            collected_count=baseline[3],
        )
        assert_run_delta(database, -1, 0, -1, 1, -1, -removed_payment[3])

        restore_payment(database, removed_payment)
        build_selection(database, INCREMENTAL_SELECTOR)
        assert_controlled_result(
            database,
            corrected_payment_id,
            baseline[0] + 1,
            baseline[3] + 1,
        )
        assert_health(
            database,
            raw_count=baseline[0] + 1,
            physical_count=baseline[0] + 1,
            current_count=baseline[0] + 1,
            absent_count=0,
            collected_count=baseline[3] + 1,
        )
        assert_run_delta(database, 1, 0, 1, -1, 1, removed_payment[3])

        build_selection(database, INCREMENTAL_SELECTOR)
        assert_controlled_result(
            database,
            corrected_payment_id,
            baseline[0] + 1,
            baseline[3] + 1,
        )
        assert_health(
            database,
            raw_count=baseline[0] + 1,
            physical_count=baseline[0] + 1,
            current_count=baseline[0] + 1,
            absent_count=0,
            collected_count=baseline[3] + 1,
        )
        assert_run_delta(database, 0, 0, 0, 0, 0, Decimal(0))
        assert health_run_count(database) == baseline_health_runs + 6
        with duckdb.connect(str(database), read_only=True) as connection:
            assert connection.execute(
                "SELECT COUNT(*) FROM audit.subscription_payment_run_delta"
            ).fetchone()[0] == baseline_health_runs + 6

        print(
            "Incremental payment check passed: unchanged input stayed stable, "
            "one late key was inserted, one existing key was updated, one absent "
            "source key was retained outside current metrics, its reappearance "
            "was restored, the final rerun remained idempotent and all six states "
            "were appended to the transformation audit with exact run-to-run "
            "count and collection differences."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    run_check(args.database)


if __name__ == "__main__":
    main()
