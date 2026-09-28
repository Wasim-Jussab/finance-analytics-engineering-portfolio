from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from finance_portfolio import generate_dbt_docs


def test_generate_docs_uses_isolated_database_copy(
    tmp_path: Path, monkeypatch
) -> None:
    source_database = tmp_path / "source.duckdb"
    docs_database = tmp_path / "docs.duckdb"
    calls: list[tuple[Path, str, tuple[str, ...]]] = []

    @contextmanager
    def fake_temporary_copy(source: Path, prefix: str) -> Iterator[Path]:
        assert source == source_database
        assert prefix == "finance-dbt-docs-"
        yield docs_database

    def fake_run_dbt(database: Path, command: str, *arguments: str) -> None:
        calls.append((database, command, arguments))

    monkeypatch.setattr(
        generate_dbt_docs, "temporary_database_copy", fake_temporary_copy
    )
    monkeypatch.setattr(generate_dbt_docs, "run_dbt", fake_run_dbt)

    generate_dbt_docs.generate_docs(source_database)

    assert calls == [(docs_database, "docs", ("generate",))]
