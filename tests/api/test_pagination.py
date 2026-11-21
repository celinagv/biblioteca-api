from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.factories import create_autor, create_libro, create_socio

Factory = Callable[[Session], Any]

RESOURCES: dict[str, Factory] = {
    "/autores": create_autor,
    "/libros": create_libro,
    "/socios": create_socio,
}


@pytest.fixture(params=RESOURCES)
def listing(request: pytest.FixtureRequest, session: Session) -> tuple[str, list[int]]:
    """Crea 25 registros del recurso y devuelve su ruta y sus ids en orden."""
    path: str = request.param
    ids = [RESOURCES[path](session).id for _ in range(25)]
    return path, ids


def _ids(response) -> list[int]:
    return [item["id"] for item in response.json()]


def test_default_page_has_20_items_ordered_by_id(
    client: TestClient, listing: tuple[str, list[int]]
) -> None:
    path, ids = listing

    assert _ids(client.get(path)) == ids[:20]


def test_limit_and_offset_select_a_window(
    client: TestClient, listing: tuple[str, list[int]]
) -> None:
    path, ids = listing

    assert _ids(client.get(path, params={"limit": 5, "offset": 10})) == ids[10:15]


def test_offset_past_the_end_returns_empty_list(
    client: TestClient, listing: tuple[str, list[int]]
) -> None:
    path, _ = listing

    assert client.get(path, params={"offset": 100}).json() == []


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_invalid_pagination_returns_422(
    client: TestClient, listing: tuple[str, list[int]], params: dict
) -> None:
    path, _ = listing

    assert client.get(path, params=params).status_code == 422
