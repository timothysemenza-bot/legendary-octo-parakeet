import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.core.startup_checks import REQUIRED_TABLES, validate_schema_state


def _create_required_tables(conn: sqlite3.Connection) -> None:
    for table in REQUIRED_TABLES:
        conn.execute(f"CREATE TABLE {table} (id TEXT PRIMARY KEY)")


def test_validate_schema_state_raises_when_tables_exist_without_alembic(tmp_path: Path) -> None:
    db_file = tmp_path / "bad_state.sqlite3"
    conn = sqlite3.connect(db_file.as_posix())
    _create_required_tables(conn)
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_file.as_posix()}")
    with pytest.raises(RuntimeError, match="not Alembic-stamped|no alembic_version|has app tables"):
        validate_schema_state(engine)


def test_validate_schema_state_passes_with_alembic_stamp(tmp_path: Path) -> None:
    db_file = tmp_path / "good_state.sqlite3"
    conn = sqlite3.connect(db_file.as_posix())
    _create_required_tables(conn)
    conn.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
    conn.execute("INSERT INTO alembic_version (version_num) VALUES ('0031_pilot_hardening_release')")
    conn.commit()
    conn.close()

    engine = create_engine(f"sqlite:///{db_file.as_posix()}")
    validate_schema_state(engine)
    with engine.connect() as check:
        assert check.execute(text("SELECT COUNT(*) FROM alembic_version")).scalar_one() == 1


def test_validate_schema_state_raises_on_empty_database(tmp_path: Path) -> None:
    db_file = tmp_path / "empty_state.sqlite3"
    sqlite3.connect(db_file.as_posix()).close()
    engine = create_engine(f"sqlite:///{db_file.as_posix()}")
    with pytest.raises(RuntimeError, match="not initialized"):
        validate_schema_state(engine)
