"""Valores fuera de rango deben dar 422, nunca un error interno (500)."""

import pytest
from fastapi.testclient import TestClient

BIG = 10**30
AUTOR = {"nombre": "X", "nacionalidad": "Y"}
LIBRO = {"titulo": "T", "isbn": "9780000000011", "stock": 1, "anio": 2000}


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", f"/autores/{BIG}", None),
        ("PUT", f"/autores/{BIG}", AUTOR),
        ("PATCH", f"/autores/{BIG}", {"nombre": "X"}),
        ("DELETE", f"/autores/{BIG}", None),
        ("GET", f"/libros/{BIG}", None),
        ("DELETE", f"/libros/{BIG}", None),
        ("GET", f"/socios/{BIG}", None),
        ("POST", f"/socios/{BIG}/baja", None),
        ("GET", f"/socios/{BIG}/prestamos", None),
        ("POST", f"/libros/{BIG}/autores/{BIG}", None),
        ("DELETE", f"/libros/{BIG}/autores/{BIG}", None),
        ("GET", f"/prestamos/{BIG}", None),
        ("POST", f"/prestamos/{BIG}/devolucion", None),
        ("GET", "/autores/0", None),
        ("GET", "/autores/-1", None),
    ],
)
def test_out_of_range_ids_in_the_url_return_422(
    client: TestClient, method: str, path: str, body: dict | None
) -> None:
    assert client.request(method, path, json=body).status_code == 422


@pytest.mark.parametrize("path", ["/autores", "/libros", "/socios"])
def test_huge_offset_returns_422(client: TestClient, path: str) -> None:
    assert client.get(path, params={"offset": BIG}).status_code == 422


@pytest.mark.parametrize(
    "payload", [{"socio_id": BIG, "libro_id": 1}, {"socio_id": 1, "libro_id": BIG}]
)
def test_huge_ids_in_the_borrow_body_return_422(client: TestClient, payload: dict) -> None:
    assert client.post("/prestamos", json=payload).status_code == 422


@pytest.mark.parametrize(("stock", "status_code"), [(1_000_000, 201), (1_000_001, 422), (BIG, 422)])
def test_stock_has_an_upper_bound(client: TestClient, stock: int, status_code: int) -> None:
    assert client.post("/libros", json={**LIBRO, "stock": stock}).status_code == status_code
