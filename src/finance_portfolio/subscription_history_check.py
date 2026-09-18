"""Prove that an agreement status change creates a new SCD Type 2 version."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import duckdb

from finance_portfolio.snapshot_scenario import (
    build_selection,
    run_snapshots,
    temporary_database_copy,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a controlled agreement change against a temporary DuckDB copy."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/finance.duckdb"),
        help="DuckDB database produced by the normal pipeline.",
    )
    return parser.parse_args()


def verify_changed_version(
    database: Path, subscription_id: str, cancellation_date: date
) -> None:
    with duckdb.connect(str(database)) as connection:
        total_versions, current_versions, closed_versions = connection.execute(
            """
            select
                count(*) as total_versions,
                count(*) filter (where dbt_valid_to is null) as current_versions,
                count(*) filter (where dbt_valid_to is not null) as closed_versions
            from history.subscription_agreement_history
            where subscription_id = ?
            """,
            [subscription_id],
        ).fetchone()

        current_status, current_cancellation_date = connection.execute(
            """
            select status, cancellation_date
            from history.subscription_agreement_history
            where subscription_id = ?
              and dbt_valid_to is null
            """,
            [subscription_id],
        ).fetchone()

        all_versions, all_current_versions = connection.execute(
            """
            select
                count(*),
                count(*) filter (where dbt_valid_to is null)
            from history.subscription_agreement_history
            """
        ).fetchone()

        status_changes = connection.execute(
            """
            select
                previous_status,
                new_status,
                business_event_date,
                observed_at,
                observation_delay_days
            from mart.fct_subscription_status_change
            where subscription_id = ?
            """,
            [subscription_id],
        ).fetchall()
        all_status_change_count = connection.execute(
            "select count(*) from mart.fct_subscription_status_change"
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

    if (total_versions, current_versions, closed_versions) != (2, 1, 1):
        raise AssertionError(
            "Expected the changed agreement to have two versions: one current and one closed."
        )
    if (all_versions, all_current_versions) != (21, 20):
        raise AssertionError("Expected 21 agreement versions with 20 current rows.")
    if (current_status, current_cancellation_date) != ("Cancelled", cancellation_date):
        raise AssertionError("The current version does not contain the controlled cancellation.")
    if len(status_changes) != 1 or all_status_change_count != 1:
        raise AssertionError("Expected exactly one observed status-change fact row.")

    previous_status, new_status, event_date, observed_at, delay_days = status_changes[0]
    expected_delay = (observed_at.date() - cancellation_date).days
    if (previous_status, new_status, event_date) != (
        "Active",
        "Cancelled",
        cancellation_date,
    ):
        raise AssertionError("The status-change fact does not describe the controlled transition.")
    if delay_days != expected_delay:
        raise AssertionError("The observation delay does not match the event and snapshot dates.")
    if len(history_events) != 1 or all_history_event_count != 1:
        raise AssertionError("Expected exactly one unified history event.")

    event_type, event_previous, event_new, event_date, is_status_change = history_events[0]
    if (
        event_type,
        event_previous,
        event_new,
        event_date,
        is_status_change,
    ) != ("Status Change", "Active", "Cancelled", cancellation_date, True):
        raise AssertionError("The unified event feed misclassified the status change.")

    print(
        "Agreement snapshot check passed: "
        "21 total agreement versions, 20 current versions, 1 closed version "
        "and 1 observed status change."
    )


def main() -> None:
    source_database = parse_args().database

    with temporary_database_copy(
        source_database, "finance-agreement-snapshot-"
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
            cancellation_date = connection.execute(
                "select as_of_date from raw.run_parameters"
            ).fetchone()[0]
            connection.execute(
                """
                update raw.subscriptions
                set status = 'Cancelled',
                    cancellation_date = ?
                where subscription_id = ?
                """,
                [cancellation_date, subscription_id],
            )

        run_snapshots(scenario_database)
        build_selection(scenario_database, "fct_subscription_status_change")
        build_selection(scenario_database, "fct_subscription_history_event")
        verify_changed_version(scenario_database, subscription_id, cancellation_date)


if __name__ == "__main__":
    main()
