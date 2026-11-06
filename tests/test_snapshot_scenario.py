from pathlib import Path

import duckdb
import pytest

from finance_portfolio import snapshot_scenario


def test_scenario_copy_refuses_unverified_file_for_known_wal_replay(
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
    before = source_database.read_bytes()

    def forbidden_copy(*args, **kwargs):
        raise AssertionError("An unverified database file must not be copied")

    monkeypatch.setattr(snapshot_scenario.shutil, "copy2", forbidden_copy)
    with pytest.raises(duckdb.CatalogException, match="Failure while replaying WAL"):
        with snapshot_scenario.temporary_database_copy(source_database, "known-wal-replay-"):
            raise AssertionError("The scenario must never start")
    assert recovery_file.read_text() == "retained for diagnosis"
    assert source_database.read_bytes() == before


def test_healthy_checkpoint_copy_retains_catalogue_name_and_data(tmp_path):
    source = tmp_path / "portfolio.duckdb"
    with duckdb.connect(str(source)) as connection:
        connection.execute(
            "create table evidence (value integer); insert into evidence values (31)"
        )
    with snapshot_scenario.temporary_database_copy(source, "healthy-copy-") as copied:
        assert copied.name == source.name
        with duckdb.connect(str(copied), read_only=True) as connection:
            assert connection.execute("select value from evidence").fetchone() == (31,)


def test_nonempty_wal_after_checkpoint_blocks_copy(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "portfolio.duckdb"
    source.write_bytes(b"synthetic database fixture")
    recovery_file = source.with_name(source.name + ".wal")

    class CheckpointConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def execute(self, statement):
            assert statement == "force checkpoint"
            recovery_file.write_bytes(b"synthetic retained WAL")

    monkeypatch.setattr(snapshot_scenario.duckdb, "connect", lambda _: CheckpointConnection())

    def forbidden_copy(*_):
        pytest.fail("Must not copy with a nonempty WAL")

    monkeypatch.setattr(snapshot_scenario.shutil, "copy2", forbidden_copy)
    with pytest.raises(RuntimeError, match="Nonempty recovery file remains"):
        with snapshot_scenario.temporary_database_copy(source, "retained-wal-"):
            pytest.fail("Must not yield a scenario database")
    assert source.read_bytes() == b"synthetic database fixture"
    assert recovery_file.read_bytes() == b"synthetic retained WAL"


def test_unrelated_catalog_error_is_not_suppressed(tmp_path: Path, monkeypatch) -> None:
    source_database = tmp_path / "portfolio.duckdb"
    source_database.touch()

    def fail_to_connect(*args, **kwargs):
        raise duckdb.CatalogException("unrelated catalogue failure")

    monkeypatch.setattr(snapshot_scenario.duckdb, "connect", fail_to_connect)

    try:
        with snapshot_scenario.temporary_database_copy(source_database, "unrelated-error-"):
            raise AssertionError("scenario copy should not be created")
    except duckdb.CatalogException as error:
        assert str(error) == "unrelated catalogue failure"
