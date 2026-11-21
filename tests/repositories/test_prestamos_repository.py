from datetime import date

from sqlmodel import Session

from repositories.libros import LibroRepository
from repositories.prestamos import PrestamoRepository
from tests.factories import create_libro, create_prestamo, create_socio


def test_take_one_from_stock_stops_at_zero(session: Session) -> None:
    libro = create_libro(session, stock=1)
    assert libro.id is not None
    repo = LibroRepository(session)

    assert repo.take_one_from_stock(libro.id) is True
    assert repo.take_one_from_stock(libro.id) is False
    session.refresh(libro)
    assert libro.stock == 0


def test_return_one_to_stock_adds_one(session: Session) -> None:
    libro = create_libro(session, stock=0)
    assert libro.id is not None

    LibroRepository(session).return_one_to_stock(libro.id)

    session.refresh(libro)
    assert libro.stock == 1


def test_mark_returned_only_works_once(session: Session) -> None:
    prestamo = create_prestamo(session, create_socio(session), create_libro(session))
    assert prestamo.id is not None
    repo = PrestamoRepository(session)

    assert repo.mark_returned(prestamo.id, date(2026, 1, 20), fine=500) is True
    assert repo.mark_returned(prestamo.id, date(2026, 1, 25), fine=900) is False
    session.refresh(prestamo)
    assert prestamo.fecha_devolucion == date(2026, 1, 20)
    assert prestamo.multa == 500


def test_count_active_by_socio_ignores_returned_prestamos(session: Session) -> None:
    socio = create_socio(session)
    assert socio.id is not None
    create_prestamo(session, socio, create_libro(session))
    create_prestamo(session, socio, create_libro(session), fecha_devolucion=date(2026, 1, 5))

    assert PrestamoRepository(session).count_active_by_socio(socio.id) == 1
