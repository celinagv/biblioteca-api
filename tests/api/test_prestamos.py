"""Un caso feliz y uno de error por cada regla de negocio del enunciado."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from models import Libro, Socio
from tests.conftest import FakeClock
from tests.factories import create_libro, create_prestamo, create_socio


def borrow(client: TestClient, socio: Socio, libro: Libro):
    return client.post("/prestamos", json={"socio_id": socio.id, "libro_id": libro.id})


def stock_of(client: TestClient, libro: Libro) -> int:
    return client.get(f"/libros/{libro.id}").json()["stock"]


# ---- Regla 4: plazo de 14 días ----


def test_rule_4_borrow_sets_dates_to_14_days(client: TestClient, session: Session) -> None:
    socio, libro = create_socio(session), create_libro(session, stock=1)

    response = borrow(client, socio, libro)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "socio_id": socio.id,
        "libro_id": libro.id,
        "fecha_prestamo": "2026-01-15",
        "fecha_vencimiento": "2026-01-29",
        "fecha_devolucion": None,
        "multa": 0,
    }


# ---- Regla 2: stock ----


def test_rule_2_borrow_takes_one_copy_from_stock(client: TestClient, session: Session) -> None:
    socio, libro = create_socio(session), create_libro(session, stock=3)

    borrow(client, socio, libro)

    assert stock_of(client, libro) == 2


def test_rule_2_borrow_without_stock_returns_409_and_creates_nothing(
    client: TestClient, session: Session
) -> None:
    socio, libro = create_socio(session), create_libro(session, stock=0)

    response = borrow(client, socio, libro)

    assert response.status_code == 409
    assert response.json() == {"detail": f"El libro {libro.id} no tiene stock disponible"}
    assert client.get(f"/socios/{socio.id}/prestamos").json() == []


def test_rule_2_the_last_copy_can_only_be_borrowed_once(
    client: TestClient, session: Session
) -> None:
    libro = create_libro(session, stock=1)

    first = borrow(client, create_socio(session), libro)
    second = borrow(client, create_socio(session), libro)

    assert (first.status_code, second.status_code) == (201, 409)
    assert stock_of(client, libro) == 0


# ---- Regla 3: socio inactivo ----


def test_rule_3_inactive_socio_cannot_borrow(client: TestClient, session: Session) -> None:
    socio, libro = create_socio(session, activo=False), create_libro(session, stock=1)

    response = borrow(client, socio, libro)

    assert response.status_code == 403
    assert stock_of(client, libro) == 1


def test_rule_3_inactive_socio_can_still_return_a_book(
    client: TestClient, session: Session
) -> None:
    socio, libro = create_socio(session), create_libro(session, stock=1)
    prestamo_id = borrow(client, socio, libro).json()["id"]
    client.post(f"/socios/{socio.id}/baja")

    assert client.post(f"/prestamos/{prestamo_id}/devolucion").status_code == 200


# ---- Regla 1: máximo 3 préstamos activos ----


def test_rule_1_a_socio_can_hold_three_active_prestamos_but_not_four(
    client: TestClient, session: Session
) -> None:
    socio = create_socio(session)
    libros = [create_libro(session, stock=1) for _ in range(4)]

    statuses = [borrow(client, socio, libro).status_code for libro in libros]

    assert statuses == [201, 201, 201, 409]
    assert stock_of(client, libros[3]) == 1


def test_rule_1_returned_prestamos_do_not_count_toward_the_limit(
    client: TestClient, session: Session
) -> None:
    socio = create_socio(session)
    for _ in range(3):
        prestamo = create_prestamo(session, socio, create_libro(session, stock=1))
        client.post(f"/prestamos/{prestamo.id}/devolucion")

    assert borrow(client, socio, create_libro(session, stock=1)).status_code == 201


# ---- Orden de las validaciones: 404 -> 403 -> 409 (límite) -> 409 (stock) ----


def test_inactive_socio_is_reported_before_the_limit(client: TestClient, session: Session) -> None:
    socio = create_socio(session, activo=False)
    for _ in range(3):
        create_prestamo(session, socio, create_libro(session))

    assert borrow(client, socio, create_libro(session, stock=1)).status_code == 403


def test_limit_is_reported_before_missing_stock(client: TestClient, session: Session) -> None:
    socio = create_socio(session)
    for _ in range(3):
        create_prestamo(session, socio, create_libro(session))

    response = borrow(client, socio, create_libro(session, stock=0))

    assert response.status_code == 409
    assert response.json() == {"detail": f"El socio {socio.id} ya tiene 3 préstamos activos"}


# ---- Regla 7: recursos inexistentes y datos inválidos ----


def test_rule_7_unknown_socio_or_libro_returns_404(client: TestClient, session: Session) -> None:
    socio, libro = create_socio(session), create_libro(session, stock=1)

    unknown_socio = client.post("/prestamos", json={"socio_id": 99, "libro_id": libro.id})
    unknown_libro = client.post("/prestamos", json={"socio_id": socio.id, "libro_id": 99})

    assert unknown_socio.status_code == 404
    assert unknown_socio.json() == {"detail": "Socio con id 99 no encontrado"}
    assert unknown_libro.status_code == 404
    assert unknown_libro.json() == {"detail": "Libro con id 99 no encontrado"}


def test_rule_7_unknown_prestamo_returns_404(client: TestClient) -> None:
    assert client.get("/prestamos/99").status_code == 404
    response = client.post("/prestamos/99/devolucion")
    assert response.status_code == 404
    assert response.json() == {"detail": "Préstamo con id 99 no encontrado"}


@pytest.mark.parametrize(
    "payload",
    [{}, {"socio_id": 1}, {"socio_id": 0, "libro_id": 1}, {"socio_id": "a", "libro_id": 1}],
    ids=["vacio", "falta-libro", "id-cero", "id-texto"],
)
def test_borrow_rejects_invalid_body(client: TestClient, payload: dict) -> None:
    assert client.post("/prestamos", json=payload).status_code == 422


# ---- Regla 5: devolución, stock y multa ----


def test_rule_5_return_restores_stock_and_records_the_date(
    client: TestClient, session: Session, clock: FakeClock
) -> None:
    socio, libro = create_socio(session), create_libro(session, stock=1)
    prestamo_id = borrow(client, socio, libro).json()["id"]
    clock.today += timedelta(days=3)

    response = client.post(f"/prestamos/{prestamo_id}/devolucion")

    assert response.status_code == 200
    assert response.json()["fecha_devolucion"] == "2026-01-18"
    assert stock_of(client, libro) == 1


@pytest.mark.parametrize(
    ("days_kept", "expected_fine"),
    [(1, 0), (14, 0), (15, 100), (19, 500)],
    ids=["antes", "el-dia-del-vencimiento", "un-dia-tarde", "cinco-dias-tarde"],
)
def test_rule_5_fine_is_100_per_day_of_delay(
    client: TestClient,
    session: Session,
    clock: FakeClock,
    days_kept: int,
    expected_fine: int,
) -> None:
    socio, libro = create_socio(session), create_libro(session, stock=1)
    prestamo_id = borrow(client, socio, libro).json()["id"]
    clock.today += timedelta(days=days_kept)

    response = client.post(f"/prestamos/{prestamo_id}/devolucion")

    assert response.json()["multa"] == expected_fine


# ---- Regla 6: no se devuelve dos veces ----


def test_rule_6_returning_twice_returns_409_and_does_not_restock_twice(
    client: TestClient, session: Session
) -> None:
    socio, libro = create_socio(session), create_libro(session, stock=1)
    prestamo_id = borrow(client, socio, libro).json()["id"]
    client.post(f"/prestamos/{prestamo_id}/devolucion")

    second = client.post(f"/prestamos/{prestamo_id}/devolucion")

    assert second.status_code == 409
    assert second.json() == {"detail": f"El préstamo {prestamo_id} ya fue devuelto"}
    assert stock_of(client, libro) == 1


def test_get_prestamo_reflects_its_current_state(client: TestClient, session: Session) -> None:
    socio, libro = create_socio(session), create_libro(session, stock=1)
    prestamo_id = borrow(client, socio, libro).json()["id"]

    assert client.get(f"/prestamos/{prestamo_id}").json()["fecha_devolucion"] is None
    client.post(f"/prestamos/{prestamo_id}/devolucion")
    assert client.get(f"/prestamos/{prestamo_id}").json()["fecha_devolucion"] == "2026-01-15"
