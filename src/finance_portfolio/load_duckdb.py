"""Load the generated CSVs into DuckDB and run the reporting SQL models."""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path
from typing import TypeAlias

import duckdb

Row: TypeAlias = dict[str, str]

RAW_TABLES: dict[str, list[tuple[str, str]]] = {
    "customers": [
        ("customer_id", "VARCHAR"),
        ("first_name", "VARCHAR"),
        ("last_name", "VARCHAR"),
        ("date_of_birth", "DATE"),
        ("postcode", "VARCHAR"),
    ],
    "loans": [
        ("account_id", "VARCHAR"),
        ("customer_id", "VARCHAR"),
        ("product_code", "VARCHAR"),
        ("origination_date", "DATE"),
        ("original_balance", "DECIMAL(12, 2)"),
        ("status", "VARCHAR"),
    ],
    "subscriptions": [
        ("subscription_id", "VARCHAR"),
        ("customer_id", "VARCHAR"),
        ("product_code", "VARCHAR"),
        ("start_date", "DATE"),
        ("cancellation_date", "DATE"),
        ("billing_frequency", "VARCHAR"),
        ("status", "VARCHAR"),
    ],
    "subscription_payments": [
        ("subscription_payment_id", "VARCHAR"),
        ("subscription_id", "VARCHAR"),
        ("billing_date", "DATE"),
        ("amount", "DECIMAL(12, 2)"),
        ("payment_status", "VARCHAR"),
    ],
    "payments": [
        ("payment_id", "VARCHAR"),
        ("account_id", "VARCHAR"),
        ("payment_date", "DATE"),
        ("amount", "DECIMAL(12, 2)"),
        ("payment_status", "VARCHAR"),
        ("payment_method", "VARCHAR"),
    ],
}


def _read_csv(path: Path) -> list[Row]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _create_raw_table(connection: duckdb.DuckDBPyConnection, table: str) -> None:
    columns = ", ".join(f"{name} {data_type}" for name, data_type in RAW_TABLES[table])
    connection.execute(f"CREATE OR REPLACE TABLE raw.{table} ({columns})")


def load_raw_tables(connection: duckdb.DuckDBPyConnection, raw_dir: Path) -> dict[str, int]:
    """Replace the raw tables from a directory of generated CSV files."""

    connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
    row_counts: dict[str, int] = {}
    for table, columns in RAW_TABLES.items():
        rows = _read_csv(raw_dir / f"{table}.csv")
        _create_raw_table(connection, table)
        column_names = [name for name, _ in columns]
        placeholders = ", ".join("?" for _ in column_names)
        values = [
            tuple(row[name] if row[name] != "" else None for name in column_names)
            for row in rows
        ]
        if values:
            connection.executemany(f"INSERT INTO raw.{table} VALUES ({placeholders})", values)
        row_counts[table] = len(rows)
    return row_counts


def _set_run_parameters(connection: duckdb.DuckDBPyConnection, as_of_date: date) -> None:
    connection.execute("CREATE OR REPLACE TABLE raw.run_parameters (as_of_date DATE)")
    connection.execute("INSERT INTO raw.run_parameters VALUES (?)", [as_of_date.isoformat()])


def run_sql_models(
    connection: duckdb.DuckDBPyConnection, sql_path: Path, as_of_date: date
) -> None:
    """Run the SQL models with a fixed as-of date for reproducible results."""

    _set_run_parameters(connection, as_of_date)
    connection.execute(sql_path.read_text(encoding="utf-8"))


def validate_database(connection: duckdb.DuckDBPyConnection) -> list[str]:
    """Return data-quality errors found after loading and modelling."""

    errors: list[str] = []
    key_fields = {
        "mart.dim_customer": "customer_id",
        "mart.dim_loan": "account_id",
        "mart.fct_payment": "payment_id",
    }
    for table, key in key_fields.items():
        duplicate_count = connection.execute(
            f"""
            SELECT COUNT(*) - COUNT(DISTINCT {key})
            FROM {table}
            """
        ).fetchone()[0]
        if duplicate_count:
            errors.append(f"{table} has {duplicate_count} duplicate {key} values")

    orphan_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM mart.fct_payment AS payment
        LEFT JOIN mart.dim_loan AS loan USING (account_id)
        WHERE loan.account_id IS NULL
        """
    ).fetchone()[0]
    if orphan_count:
        errors.append(f"mart.fct_payment has {orphan_count} orphan account references")

    raw_total, fact_total, summary_total = connection.execute(
        """
        SELECT
            COALESCE((
                SELECT SUM(amount) FROM raw.payments WHERE payment_status = 'Completed'
            ), 0),
            COALESCE((
                SELECT SUM(amount) FROM mart.fct_payment WHERE is_successful
            ), 0),
            COALESCE((SELECT SUM(completed_payment_amount) FROM mart.dim_loan), 0)
        """
    ).fetchone()
    if raw_total != fact_total:
        errors.append(
            "completed payment fact total does not reconcile: "
            f"raw={raw_total} fact={fact_total}"
        )
    if raw_total != summary_total:
        errors.append(
            "completed payment loan summary does not reconcile: "
            f"raw={raw_total} summary={summary_total}"
        )
    return errors


def build_database(
    raw_dir: Path,
    database_path: Path,
    sql_path: Path,
    as_of_date: date,
) -> dict[str, int]:
    """Build a fresh local DuckDB file and return the resulting table counts."""

    database_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(database_path)) as connection:
        load_raw_tables(connection, raw_dir)
        run_sql_models(connection, sql_path, as_of_date)
        errors = validate_database(connection)
        if errors:
            raise ValueError("Database validation failed:\n- " + "\n- ".join(errors))

        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "raw.customers",
                "raw.loans",
                "raw.subscriptions",
                "raw.subscription_payments",
                "raw.payments",
                "mart.dim_customer",
                "mart.dim_loan",
                "mart.fct_payment",
            )
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Load generated CSVs into a local DuckDB database")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/generated"))
    parser.add_argument("--database", type=Path, default=Path("data/finance.duckdb"))
    parser.add_argument("--sql", type=Path, default=Path("sql/duckdb/marts.sql"))
    parser.add_argument("--as-of", type=date.fromisoformat, default=date(2025, 12, 31))
    args = parser.parse_args()

    counts = build_database(args.raw_dir, args.database, args.sql, args.as_of)
    for table, count in counts.items():
        print(f"{table}: {count} rows")
    print(f"database: {args.database}")


if __name__ == "__main__":
    main()
