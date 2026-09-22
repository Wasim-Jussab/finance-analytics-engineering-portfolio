"""Shared helpers for controlled dbt snapshot scenarios."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb


@contextmanager
def temporary_database_copy(source_database: Path, prefix: str) -> Iterator[Path]:
    """Yield an isolated copy of a completed local pipeline database."""
    source_database = source_database.resolve()
    if not source_database.exists():
        raise FileNotFoundError(
            f"Database not found: {source_database}. Run 'make pipeline' first."
        )

    with duckdb.connect(str(source_database)) as connection:
        connection.execute("force checkpoint")

    with tempfile.TemporaryDirectory(prefix=prefix) as temp_directory:
        # Persisted DuckDB views can store the database catalogue name. Keep it
        # unchanged when running a scenario against a non-default database path.
        scenario_database = Path(temp_directory) / source_database.name
        shutil.copy2(source_database, scenario_database)
        yield scenario_database


def run_dbt(database: Path, command: str, *arguments: str) -> None:
    """Run one dbt command against the supplied DuckDB database."""
    env = os.environ.copy()
    env["FINANCE_DUCKDB_PATH"] = str(database)
    subprocess.run(
        [
            "dbt",
            command,
            *arguments,
            "--project-dir",
            ".",
            "--profiles-dir",
            "config",
            "--target",
            "local",
            "--no-partial-parse",
        ],
        check=True,
        env=env,
    )


def run_snapshots(database: Path) -> None:
    """Run every project snapshot against the supplied DuckDB database."""
    run_dbt(database, "snapshot")


def run_selection(database: Path, selector: str) -> None:
    """Run one selected model without pulling downstream tests forward."""
    run_dbt(database, "run", "--select", selector)


def build_selection(database: Path, selector: str) -> None:
    """Build and test one selected dbt resource."""
    run_dbt(database, "build", "--select", selector)
