"""Prove that an agreement status change creates a new SCD Type 2 version."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import duckdb

from finance_portfolio.snapshot_scenario import run_snapshots, temporary_database_copy


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

    if (total_versions, current_versions, closed_versions) != (2, 1, 1):
        raise AssertionError(
            "Expected the changed agreement to have two versions: one current and one closed."
        )
    if (all_versions, all_current_versions) != (21, 20):
        raise AssertionError("Expected 21 agreement versions with 20 current rows.")
    if (current_status, current_cancellation_date) != ("Cancelled", cancellation_date):
        raise AssertionError("The current version does not contain the controlled cancellation.")

    print(
        "Agreement snapshot check passed: "
        "21 total agreement versions, 20 current versions and 1 closed version."
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
        verify_changed_version(scenario_database, subscription_id, cancellation_date)


if __name__ == "__main__":
    main()
