import pytest
from sqlalchemy.engine import Engine
from sqlmodel import Session

import database


def test_sqlite_enforces_foreign_keys(session: Session) -> None:
    result = session.connection().exec_driver_sql("PRAGMA foreign_keys").scalar()

    assert result == 1


def test_get_session_yields_a_session(monkeypatch: pytest.MonkeyPatch, engine: Engine) -> None:
    monkeypatch.setattr(database, "engine", engine)

    generator = database.get_session()
    session = next(generator)

    assert isinstance(session, Session)
    generator.close()


def test_create_db_and_tables_is_idempotent(
    monkeypatch: pytest.MonkeyPatch, engine: Engine
) -> None:
    monkeypatch.setattr(database, "engine", engine)

    database.create_db_and_tables()
    database.create_db_and_tables()
