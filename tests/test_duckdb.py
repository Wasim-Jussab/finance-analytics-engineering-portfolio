from datetime import date
from pathlib import Path

import duckdb

from finance_portfolio.generate_data import (
    GeneratorConfig,
    generate_dataset,
    write_dataset,
)
from finance_portfolio.load_duckdb import build_database, validate_database

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
    assert counts["raw.customers"] == 10
    assert counts["raw.loans"] == 10
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
