from pathlib import Path

import duckdb

from finance_portfolio import snapshot_scenario


def test_scenario_copy_uses_checkpointed_file_for_known_wal_replay(
    tmp_path: Path, monkeypatch
) -> None:
    source_database = tmp_path / "portfolio.duckdb"
    with duckdb.connect(str(source_database)) as connection:
        connection.execute("create table evidence (value integer)")
        connection.execute("insert into evidence values (31)")
        connection.execute("force checkpoint")

    recovery_file = Path(f"{source_database}.wal")
    recovery_file.write_text("retained for diagnosis", encoding="utf-8")
    real_connect = snapshot_scenario.duckdb.connect

    def connect_with_known_source_failure(database, *args, **kwargs):
        if Path(database) == source_database:
            raise duckdb.CatalogException(
                f'Failure while replaying WAL file "{recovery_file}": '
                'Schema with name "history" already exists!'
            )
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(snapshot_scenario.duckdb, "connect", connect_with_known_source_failure)

    with snapshot_scenario.temporary_database_copy(
        source_database, "known-wal-replay-"
    ) as scenario_database:
        assert scenario_database.name == source_database.name
        with real_connect(str(scenario_database), read_only=True) as connection:
            assert connection.execute("select value from evidence").fetchone() == (31,)

    assert recovery_file.exists()


def test_unrelated_catalog_error_is_not_suppressed(tmp_path: Path, monkeypatch) -> None:
    source_database = tmp_path / "portfolio.duckdb"
    source_database.touch()

    def fail_to_connect(*args, **kwargs):
        raise duckdb.CatalogException("unrelated catalogue failure")

    monkeypatch.setattr(snapshot_scenario.duckdb, "connect", fail_to_connect)

    try:
        with snapshot_scenario.temporary_database_copy(
            source_database, "unrelated-error-"
        ):
            raise AssertionError("scenario copy should not be created")
    except duckdb.CatalogException as error:
        assert str(error) == "unrelated catalogue failure"
