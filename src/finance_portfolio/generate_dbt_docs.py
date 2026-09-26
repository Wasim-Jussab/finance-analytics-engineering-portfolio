"""Generate dbt documentation from an isolated DuckDB database copy."""

from __future__ import annotations

import argparse
from pathlib import Path

from finance_portfolio.snapshot_scenario import run_dbt, temporary_database_copy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate dbt documentation without replaying a retained DuckDB WAL."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/finance.duckdb"),
        help="DuckDB database produced by the normal pipeline.",
    )
    return parser.parse_args()


def generate_docs(source_database: Path) -> None:
    """Run dbt docs generation against a checkpointed temporary copy."""
    with temporary_database_copy(source_database, "finance-dbt-docs-") as docs_database:
        run_dbt(docs_database, "docs", "generate")


def main() -> None:
    generate_docs(parse_args().database)


if __name__ == "__main__":
    main()
