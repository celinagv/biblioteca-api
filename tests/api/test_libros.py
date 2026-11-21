from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.factories import create_libro, create_prestamo, create_socio

PAYLOAD = {"titulo": "Ficciones", "isbn": "9780802130303", "stock": 3, "anio": 1944}


def test_create_returns_201_with_generated_id(client: TestClient) -> None:
    response = client.post("/libros", json=PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {"id": 1, **PAYLOAD, "autores": []}


def test_create_defaults_stock_to_zero(client: TestClient) -> None:
    body = {k: v for k, v in PAYLOAD.items() if k != "stock"}

    assert client.post("/libros", json=body).json()["stock"] == 0


def test_create_stores_isbn_without_hyphens(client: TestClient) -> None:
    response = client.post("/libros", json={**PAYLOAD, "isbn": "978-0-8021-3030-3"})

    assert response.json()["isbn"] == "9780802130303"


def test_create_rejects_duplicate_isbn_even_with_different_format(client: TestClient) -> None:
    client.post("/libros", json=PAYLOAD)

    response = client.post("/libros", json={**PAYLOAD, "isbn": "978-0-8021-3030-3"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Ya existe un libro con el ISBN 9780802130303"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"isbn": "123"},
        {"isbn": "abcdefghij"},
        {"stock": -1},
        {"anio": 0},
        {"anio": date.today().year + 1},
        {"titulo": "  "},
    ],
    ids=["isbn-corto", "isbn-letras", "stock-negativo", "anio-cero", "anio-futuro", "titulo-vacio"],
)
def test_create_rejects_invalid_data(client: TestClient, overrides: dict) -> None:
    assert client.post("/libros", json={**PAYLOAD, **overrides}).status_code == 422


def test_get_and_404(client: TestClient, session: Session) -> None:
    libro = create_libro(session)

    assert client.get(f"/libros/{libro.id}").status_code == 200
    assert client.get("/libros/99").status_code == 404


def test_put_replaces_all_fields(client: TestClient, session: Session) -> None:
    libro = create_libro(session)

    response = client.put(f"/libros/{libro.id}", json=PAYLOAD)

    assert response.json() == {"id": libro.id, **PAYLOAD, "autores": []}


def test_put_requires_every_field(client: TestClient, session: Session) -> None:
    libro = create_libro(session)
    body = {k: v for k, v in PAYLOAD.items() if k != "stock"}

    assert client.put(f"/libros/{libro.id}", json=body).status_code == 422


def test_put_allows_keeping_own_isbn(client: TestClient, session: Session) -> None:
    libro = create_libro(session, isbn=PAYLOAD["isbn"])

    assert client.put(f"/libros/{libro.id}", json=PAYLOAD).status_code == 200


def test_put_rejects_isbn_of_another_libro(client: TestClient, session: Session) -> None:
    create_libro(session, isbn=PAYLOAD["isbn"])
    libro = create_libro(session)

    assert client.put(f"/libros/{libro.id}", json=PAYLOAD).status_code == 409


def test_patch_changes_only_sent_fields(client: TestClient, session: Session) -> None:
    libro = create_libro(session, titulo="Original", stock=1)

    response = client.patch(f"/libros/{libro.id}", json={"stock": 7})

    assert response.json()["stock"] == 7
    assert response.json()["titulo"] == "Original"


def test_patch_rejects_isbn_of_another_libro(client: TestClient, session: Session) -> None:
    create_libro(session, isbn=PAYLOAD["isbn"])
    libro = create_libro(session)

    assert client.patch(f"/libros/{libro.id}", json={"isbn": PAYLOAD["isbn"]}).status_code == 409


def test_patch_validates_each_field(client: TestClient, session: Session) -> None:
    libro = create_libro(session)

    assert client.patch(f"/libros/{libro.id}", json={"stock": -5}).status_code == 422
    assert client.patch(f"/libros/{libro.id}", json={"titulo": None}).status_code == 422


def test_delete_removes_a_libro_without_prestamos(client: TestClient, session: Session) -> None:
    libro = create_libro(session)

    assert client.delete(f"/libros/{libro.id}").status_code == 204
    assert client.get(f"/libros/{libro.id}").status_code == 404


def test_delete_with_prestamos_returns_409_and_keeps_the_libro(
    client: TestClient, session: Session
) -> None:
    libro = create_libro(session)
    create_prestamo(session, create_socio(session), libro)

    response = client.delete(f"/libros/{libro.id}")

    assert response.status_code == 409
    assert client.get(f"/libros/{libro.id}").status_code == 200


def test_delete_unknown_returns_404(client: TestClient) -> None:
    assert client.delete("/libros/99").status_code == 404


@pytest.mark.parametrize(
    ("params", "expected_stocks"),
    [
        ({"disponibles": "true"}, [2, 5]),
        ({"disponibles": "false"}, [0, 0]),
        ({}, [2, 0, 5, 0]),
        ({"disponibles": "true", "limit": 1, "offset": 1}, [5]),
    ],
    ids=["con-stock", "sin-stock", "todos", "combinado-con-paginacion"],
)
def test_list_filters_by_availability(
    client: TestClient, session: Session, params: dict, expected_stocks: list[int]
) -> None:
    for stock in (2, 0, 5, 0):
        create_libro(session, stock=stock)

    response = client.get("/libros", params=params)

    assert [libro["stock"] for libro in response.json()] == expected_stocks


def test_list_rejects_invalid_disponibles(client: TestClient) -> None:
    assert client.get("/libros", params={"disponibles": "quizas"}).status_code == 422
