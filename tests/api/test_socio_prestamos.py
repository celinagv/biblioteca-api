import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.factories import create_libro, create_prestamo, create_socio


def _ids(response) -> list[int]:
    return [p["id"] for p in response.json()]


@pytest.fixture
def socio_with_prestamos(session: Session):
    """Socio con 3 préstamos (el 2º ya devuelto) y otro socio con uno propio."""
    socio = create_socio(session)
    first = create_prestamo(session, socio, create_libro(session))
    second = create_prestamo(
        session, socio, create_libro(session), fecha_devolucion=first.fecha_prestamo
    )
    third = create_prestamo(session, socio, create_libro(session))
    create_prestamo(session, create_socio(session), create_libro(session))
    return socio, [first.id, second.id, third.id]


def test_lists_only_the_prestamos_of_that_socio_ordered_by_id(
    client: TestClient, socio_with_prestamos
) -> None:
    socio, ids = socio_with_prestamos

    assert _ids(client.get(f"/socios/{socio.id}/prestamos")) == ids


def test_activos_true_returns_only_unreturned_prestamos(
    client: TestClient, socio_with_prestamos
) -> None:
    socio, ids = socio_with_prestamos

    response = client.get(f"/socios/{socio.id}/prestamos", params={"activos": "true"})

    assert _ids(response) == [ids[0], ids[2]]


def test_activos_false_returns_only_returned_prestamos(
    client: TestClient, socio_with_prestamos
) -> None:
    socio, ids = socio_with_prestamos

    response = client.get(f"/socios/{socio.id}/prestamos", params={"activos": "false"})

    assert _ids(response) == [ids[1]]


def test_list_is_paginated(client: TestClient, socio_with_prestamos) -> None:
    socio, ids = socio_with_prestamos

    response = client.get(f"/socios/{socio.id}/prestamos", params={"limit": 1, "offset": 2})

    assert _ids(response) == [ids[2]]


def test_socio_without_prestamos_returns_empty_list(client: TestClient, session: Session) -> None:
    socio = create_socio(session)

    assert client.get(f"/socios/{socio.id}/prestamos").json() == []


def test_unknown_socio_returns_404(client: TestClient) -> None:
    response = client.get("/socios/99/prestamos")

    assert response.status_code == 404
    assert response.json() == {"detail": "Socio con id 99 no encontrado"}


def test_invalid_activos_returns_422(client: TestClient, session: Session) -> None:
    socio = create_socio(session)

    assert (
        client.get(f"/socios/{socio.id}/prestamos", params={"activos": "tal-vez"}).status_code
        == 422
    )
