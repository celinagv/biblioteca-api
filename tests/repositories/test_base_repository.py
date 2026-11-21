import pytest
from sqlmodel import Session

from exceptions import ConflictError
from models import Libro
from repositories.libros import LibroRepository
from repositories.socios import SocioRepository
from tests.factories import create_libro, create_prestamo, create_socio


def test_duplicate_unique_value_becomes_conflict_error(session: Session) -> None:
    create_libro(session, isbn="9780802130303")

    with pytest.raises(ConflictError):
        LibroRepository(session).save(
            Libro(titulo="Otro", isbn="9780802130303", stock=1, anio=2000)
        )


def test_database_rejects_negative_stock(session: Session) -> None:
    with pytest.raises(ConflictError):
        LibroRepository(session).save(Libro(titulo="X", isbn="9780000000001", stock=-1, anio=2000))


def test_database_rejects_deleting_a_referenced_socio(session: Session) -> None:
    socio = create_socio(session)
    create_prestamo(session, socio, create_libro(session))

    with pytest.raises(ConflictError):
        SocioRepository(session).delete(socio)


def test_session_stays_usable_after_a_conflict(session: Session) -> None:
    repo = LibroRepository(session)
    with pytest.raises(ConflictError):
        repo.save(Libro(titulo="X", isbn="9780000000001", stock=-1, anio=2000))

    assert repo.save(Libro(titulo="Y", isbn="9780000000002", stock=1, anio=2000)).id is not None
