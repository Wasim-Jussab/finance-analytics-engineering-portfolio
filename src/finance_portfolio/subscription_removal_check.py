"""Prove that a missing agreement is closed without being called cancelled."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

from finance_portfolio.snapshot_scenario import (
    build_selection,
    run_selection,
    run_snapshots,
    temporary_database_copy,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a controlled source removal against a temporary DuckDB copy."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/finance.duckdb"),
        help="DuckDB database produced by the normal pipeline.",
    )
    return parser.parse_args()


def verify_removal(database: Path, subscription_id: str) -> None:
    with duckdb.connect(str(database)) as connection:
        target_versions, target_current, target_closed = connection.execute(
            """
            select
                count(*),
                count(*) filter (where dbt_valid_to is null),
                count(*) filter (where dbt_valid_to is not null)
            from history.subscription_agreement_history
            where subscription_id = ?
            """,
            [subscription_id],
        ).fetchone()

        all_versions, all_current = connection.execute(
            """
            select
                count(*),
                count(*) filter (where dbt_valid_to is null)
            from history.subscription_agreement_history
            """
        ).fetchone()

        removals = connection.execute(
            """
            select
                last_observed_status,
                last_observed_cancellation_date,
                removed_at,
                was_cancelled_before_removal
            from mart.fct_subscription_source_removal
            where subscription_id = ?
            """,
            [subscription_id],
        ).fetchall()
        all_removal_count = connection.execute(
            "select count(*) from mart.fct_subscription_source_removal"
        ).fetchone()[0]

        history_events = connection.execute(
            """
            select
                event_type,
                previous_status,
                new_status,
                business_event_date,
                is_business_status_change
            from mart.fct_subscription_history_event
            where subscription_id = ?
            """,
            [subscription_id],
        ).fetchall()
        all_history_event_count = connection.execute(
            "select count(*) from mart.fct_subscription_history_event"
        ).fetchone()[0]

    if (target_versions, target_current, target_closed) != (1, 0, 1):
        raise AssertionError("Expected the removed agreement to have one closed version.")
    if (all_versions, all_current) != (20, 19):
        raise AssertionError("Expected 20 agreement versions with 19 current rows.")
    if len(removals) != 1 or all_removal_count != 1:
        raise AssertionError("Expected exactly one source-removal fact row.")

    status, cancellation_date, removed_at, was_cancelled = removals[0]
    if status != "Active" or cancellation_date is not None:
        raise AssertionError("The scenario did not retain the last observed active state.")
    if removed_at is None or was_cancelled:
        raise AssertionError("Source removal was incorrectly represented as cancellation.")
    if len(history_events) != 1 or all_history_event_count != 1:
        raise AssertionError("Expected exactly one unified history event.")

    event_type, event_previous, event_new, event_date, is_status_change = history_events[0]
    if (
        event_type,
        event_previous,
        event_new,
        event_date,
        is_status_change,
    ) != ("Source Removal", "Active", None, None, False):
        raise AssertionError("The unified event feed misclassified the source removal.")

    print(
        "Source removal check passed: "
        "20 agreement versions, 19 current versions, 1 closed version "
        "and 1 removal that is not labelled as a cancellation."
    )


def main() -> None:
    source_database = parse_args().database

    with temporary_database_copy(
        source_database, "finance-removal-snapshot-"
    ) as scenario_database:
        with duckdb.connect(str(scenario_database)) as connection:
            row = connection.execute(
                """
                select subscription_id
                from raw.subscriptions
                where status = 'Active'
                  and cancellation_date is null
                order by subscription_id
                limit 1
                """
            ).fetchone()
            if row is None:
                raise AssertionError("No active subscription is available for the scenario.")

            subscription_id = row[0]
            connection.execute(
                "delete from raw.subscriptions where subscription_id = ?",
                [subscription_id],
            )

        run_snapshots(scenario_database)
        run_selection(scenario_database, "fct_subscription_source_removal")
        build_selection(scenario_database, "fct_subscription_history_event")
        verify_removal(scenario_database, subscription_id)


if __name__ == "__main__":
    main()
