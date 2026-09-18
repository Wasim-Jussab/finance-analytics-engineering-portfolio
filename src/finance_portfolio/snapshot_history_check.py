"""Prove that a changed plan creates a new SCD Type 2 version."""

from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path

import duckdb

from finance_portfolio.snapshot_scenario import run_snapshots, temporary_database_copy

PLAN_ID = "SUB-1-MONTHLY"
CHANGE_AMOUNT = Decimal("0.01")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a controlled plan change against a temporary DuckDB copy."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/finance.duckdb"),
        help="DuckDB database produced by the normal pipeline.",
    )
    return parser.parse_args()


def verify_changed_version(database: Path, baseline_amount: Decimal) -> None:
    with duckdb.connect(str(database)) as connection:
        total_versions, current_versions, closed_versions = connection.execute(
            """
            select
                count(*) as total_versions,
                count(*) filter (where dbt_valid_to is null) as current_versions,
                count(*) filter (where dbt_valid_to is not null) as closed_versions
            from history.subscription_plan_history
            where subscription_plan_id = ?
            """,
            [PLAN_ID],
        ).fetchone()

        current_amount = connection.execute(
            """
            select billing_amount
            from history.subscription_plan_history
            where subscription_plan_id = ?
              and dbt_valid_to is null
            """,
            [PLAN_ID],
        ).fetchone()[0]

        all_current_versions = connection.execute(
            """
            select count(*)
            from history.subscription_plan_history
            where dbt_valid_to is null
            """
        ).fetchone()[0]

    expected_amount = baseline_amount + CHANGE_AMOUNT
    if (total_versions, current_versions, closed_versions) != (2, 1, 1):
        raise AssertionError(
            "Expected the changed plan to have two versions: one current and one closed."
        )
    if all_current_versions != 4:
        raise AssertionError("Expected exactly one current version for each of the four plans.")
    if current_amount != expected_amount:
        raise AssertionError(
            f"Expected current amount {expected_amount}, found {current_amount}."
        )

    print(
        "Plan snapshot check passed: "
        "5 total plan versions, 4 current versions and 1 closed version."
    )


def main() -> None:
    source_database = parse_args().database

    with temporary_database_copy(source_database, "finance-plan-snapshot-") as scenario_database:
        with duckdb.connect(str(scenario_database)) as connection:
            row = connection.execute(
                """
                select billing_amount
                from raw.subscription_plans
                where subscription_plan_id = ?
                """,
                [PLAN_ID],
            ).fetchone()
            if row is None:
                raise AssertionError(f"Plan {PLAN_ID} was not found.")

            baseline_amount = row[0]
            connection.execute(
                """
                update raw.subscription_plans
                set billing_amount = billing_amount + ?
                where subscription_plan_id = ?
                """,
                [CHANGE_AMOUNT, PLAN_ID],
            )

        run_snapshots(scenario_database)
        verify_changed_version(scenario_database, baseline_amount)


if __name__ == "__main__":
    main()
