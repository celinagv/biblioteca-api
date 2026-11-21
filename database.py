import sqlite3
from collections.abc import Generator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.pool import ConnectionPoolEntry
from sqlmodel import Session, SQLModel, create_engine

import models  # noqa: F401  (necesario para que SQLModel conozca todas las tablas)
from config import get_settings


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(
    dbapi_connection: DBAPIConnection, _record: ConnectionPoolEntry
) -> None:
    # En SQLite las claves foráneas vienen desactivadas: hay que habilitarlas en cada conexión
    if isinstance(dbapi_connection, sqlite3.Connection):
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


def _build_engine(url: str) -> Engine:
    # check_same_thread es una opción propia de SQLite; con otros motores no se envía nada
    driver_options = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=driver_options)


engine = _build_engine(get_settings().database_url)


def create_db_and_tables() -> None:
    """Crea en la base las tablas registradas en el metadata (no toca las existentes)."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Entrega una sesión por request y la cierra al terminar."""
    with Session(engine) as session:
        yield session
