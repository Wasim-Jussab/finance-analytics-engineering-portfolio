from datetime import date
from pathlib import Path

import duckdb
import pytest

from finance_portfolio.generate_data import (
    GeneratorConfig,
    generate_dataset,
    write_dataset,
)
from finance_portfolio.load_duckdb import RAW_TABLES, build_database, validate_database

SQL_PATH = Path(__file__).parents[1] / "sql/duckdb/marts.sql"


def test_duckdb_build_loads_raw_and_reporting_tables(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    database_path = tmp_path / "finance.duckdb"
    write_dataset(generate_dataset(GeneratorConfig(seed=42, customer_count=10)), raw_dir)

    counts = build_database(
        raw_dir,
        database_path,
        SQL_PATH,
        date(2025, 12, 31),
    )

    assert database_path.exists()
    assert counts["raw.subscription_plans"] == 4
    assert counts["raw.customers"] == 10
    assert counts["raw.loans"] == 10
    assert counts["raw.subscription_payments"] > 0
    assert counts["raw.ingestion_audit"] == 7
    assert counts["mart.dim_customer"] == 10
    assert counts["mart.dim_loan"] == 10
    assert counts["mart.fct_payment"] > 0

    with duckdb.connect(str(database_path)) as connection:
        assert validate_database(connection) == []
        assert connection.execute(
            "SELECT COUNT(*) FROM mart.fct_payment WHERE NOT is_successful"
        ).fetchone()[0] > 0


def test_duckdb_as_of_date_is_explicit(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    database_path = tmp_path / "finance.duckdb"
    write_dataset(generate_dataset(GeneratorConfig(seed=7, customer_count=2)), raw_dir)

    build_database(
        raw_dir,
        database_path,
        SQL_PATH,
        date(2025, 12, 31),
    )
    with duckdb.connect(str(database_path)) as connection:
        first_age = connection.execute(
            "SELECT loan_age_months FROM mart.dim_loan ORDER BY account_id LIMIT 1"
        ).fetchone()[0]

    build_database(
        raw_dir,
        database_path,
        SQL_PATH,
        date(2026, 12, 31),
    )
    with duckdb.connect(str(database_path)) as connection:
        second_age = connection.execute(
            "SELECT loan_age_months FROM mart.dim_loan ORDER BY account_id LIMIT 1"
        ).fetchone()[0]

    assert second_age >= first_age


def test_raw_tables_record_one_load_timestamp(tmp_path) -> None:
    raw_dir = tmp_path / "raw"
    database_path = tmp_path / "finance.duckdb"
    write_dataset(generate_dataset(GeneratorConfig(seed=42, customer_count=5)), raw_dir)

    build_database(
        raw_dir,
        database_path,
        SQL_PATH,
        date(2025, 12, 31),
    )

    with duckdb.connect(str(database_path)) as connection:
        timestamps = {
            connection.execute(f"SELECT DISTINCT loaded_at FROM raw.{table}").fetchone()[0]
            for table in RAW_TABLES
        }
        timestamps.add(
            connection.execute("SELECT loaded_at FROM raw.run_parameters").fetchone()[0]
        )
        load_ids = {
            connection.execute(f"SELECT DISTINCT load_id FROM raw.{table}").fetchone()[0]
            for table in RAW_TABLES
        }
        load_ids.add(connection.execute("SELECT load_id FROM raw.run_parameters").fetchone()[0])
        audit_summary = connection.execute(
            """
            SELECT COUNT(*), COUNT(DISTINCT load_id), COUNT(DISTINCT loaded_at)
            FROM raw.ingestion_audit
            """
        ).fetchone()

    assert None not in timestamps
    assert len(timestamps) == 1
    assert None not in load_ids
    assert len(load_ids) == 1
    assert audit_summary == (7, 1, 1)


def test_failed_load_rolls_back_to_previous_batch(tmp_path) -> None:
    first_raw_dir = tmp_path / "first_raw"
    broken_raw_dir = tmp_path / "broken_raw"
    database_path = tmp_path / "finance.duckdb"
    write_dataset(generate_dataset(GeneratorConfig(seed=42, customer_count=5)), first_raw_dir)
    write_dataset(generate_dataset(GeneratorConfig(seed=7, customer_count=7)), broken_raw_dir)

    build_database(first_raw_dir, database_path, SQL_PATH, date(2025, 12, 31))
    with duckdb.connect(str(database_path)) as connection:
        first_load_id = connection.execute(
            "SELECT DISTINCT load_id FROM raw.ingestion_audit"
        ).fetchone()[0]

    (broken_raw_dir / "payments.csv").unlink()
    with pytest.raises(FileNotFoundError):
        build_database(broken_raw_dir, database_path, SQL_PATH, date(2025, 12, 31))

    with duckdb.connect(str(database_path)) as connection:
        retained_load_id = connection.execute(
            "SELECT DISTINCT load_id FROM raw.ingestion_audit"
        ).fetchone()[0]
        retained_customer_count = connection.execute(
            "SELECT COUNT(*) FROM raw.customers"
        ).fetchone()[0]

    assert retained_load_id == first_load_id
    assert retained_customer_count == 5
