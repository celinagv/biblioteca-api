from datetime import date

import pytest
from sqlmodel import Session

from api.schemas.prestamo import PrestamoCreate
from config import Settings
from exceptions import ConflictError
from repositories.libros import LibroRepository
from repositories.prestamos import PrestamoRepository
from repositories.socios import SocioRepository
from services.prestamos import PrestamoService, calculate_fine
from tests.factories import create_libro, create_socio

TODAY = date(2026, 3, 1)


@pytest.mark.parametrize(
    ("returned_on", "expected"),
    [
        (date(2026, 3, 1), 0),
        (date(2026, 3, 15), 0),
        (date(2026, 3, 16), 100),
        (date(2026, 3, 25), 1000),
    ],
)
def test_calculate_fine(returned_on: date, expected: int) -> None:
    assert calculate_fine(date(2026, 3, 15), returned_on, daily_rate=100) == expected


def _service(session: Session, settings: Settings) -> PrestamoService:
    return PrestamoService(
        PrestamoRepository(session),
        SocioRepository(session),
        LibroRepository(session),
        settings,
    )


def test_business_rules_come_from_the_settings(session: Session) -> None:
    settings = Settings(plazo_prestamo_dias=7, multa_por_dia=50, max_prestamos_activos=1)
    service = _service(session, settings)
    socio = create_socio(session)
    libros = [create_libro(session, stock=1) for _ in range(2)]
    assert socio.id is not None
    assert libros[0].id is not None
    assert libros[1].id is not None

    prestamo = service.create(PrestamoCreate(socio_id=socio.id, libro_id=libros[0].id), TODAY)
    with pytest.raises(ConflictError, match="ya tiene 1 préstamos activos"):
        service.create(PrestamoCreate(socio_id=socio.id, libro_id=libros[1].id), TODAY)

    assert prestamo.fecha_vencimiento == date(2026, 3, 8)
    assert prestamo.id is not None
    returned = service.return_loan(prestamo.id, date(2026, 3, 10))
    assert returned.multa == 100


def test_return_loses_the_race_when_another_request_returned_it_first(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(session, Settings())
    socio, libro = create_socio(session), create_libro(session, stock=1)
    assert socio.id is not None
    assert libro.id is not None
    prestamo = service.create(PrestamoCreate(socio_id=socio.id, libro_id=libro.id), TODAY)
    assert prestamo.id is not None
    # Simula que otra request marcó la devolución justo entre la lectura y la escritura
    monkeypatch.setattr(PrestamoRepository, "mark_returned", lambda *_args, **_kwargs: False)

    with pytest.raises(ConflictError, match="ya fue devuelto"):
        service.return_loan(prestamo.id, TODAY)

    session.refresh(libro)
    assert libro.stock == 0  # no se repuso stock
