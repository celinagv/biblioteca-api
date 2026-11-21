import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.factories import create_autor

PAYLOAD = {"nombre": "Jorge Luis Borges", "nacionalidad": "Argentina"}


def test_create_returns_201_with_generated_id(client: TestClient) -> None:
    response = client.post("/autores", json=PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {"id": 1, **PAYLOAD}


@pytest.mark.parametrize(
    "payload",
    [
        {"nacionalidad": "Argentina"},
        {"nombre": "   ", "nacionalidad": "Argentina"},
        {"nombre": "x" * 101, "nacionalidad": "Argentina"},
    ],
    ids=["falta-nombre", "nombre-vacio", "nombre-largo"],
)
def test_create_rejects_invalid_data(client: TestClient, payload: dict) -> None:
    assert client.post("/autores", json=payload).status_code == 422


def test_get_returns_the_autor(client: TestClient, session: Session) -> None:
    autor = create_autor(session, nombre="Ana")

    response = client.get(f"/autores/{autor.id}")

    assert response.status_code == 200
    assert response.json()["nombre"] == "Ana"


def test_get_unknown_returns_404(client: TestClient) -> None:
    response = client.get("/autores/99")

    assert response.status_code == 404
    assert response.json() == {"detail": "Autor con id 99 no encontrado"}


def test_put_replaces_all_fields(client: TestClient, session: Session) -> None:
    autor = create_autor(session)

    response = client.put(f"/autores/{autor.id}", json=PAYLOAD)

    assert response.status_code == 200
    assert response.json() == {"id": autor.id, **PAYLOAD}


def test_put_requires_every_field(client: TestClient, session: Session) -> None:
    autor = create_autor(session)

    assert client.put(f"/autores/{autor.id}", json={"nombre": "X"}).status_code == 422


def test_put_unknown_returns_404(client: TestClient) -> None:
    assert client.put("/autores/99", json=PAYLOAD).status_code == 404


def test_patch_changes_only_sent_fields(client: TestClient, session: Session) -> None:
    autor = create_autor(session, nombre="Ana", nacionalidad="Chilena")

    response = client.patch(f"/autores/{autor.id}", json={"nacionalidad": "Uruguaya"})

    assert response.json() == {"id": autor.id, "nombre": "Ana", "nacionalidad": "Uruguaya"}


def test_patch_with_empty_body_changes_nothing(client: TestClient, session: Session) -> None:
    autor = create_autor(session, nombre="Ana")

    response = client.patch(f"/autores/{autor.id}", json={})

    assert response.status_code == 200
    assert response.json()["nombre"] == "Ana"


def test_patch_rejects_explicit_null(client: TestClient, session: Session) -> None:
    autor = create_autor(session)

    response = client.patch(f"/autores/{autor.id}", json={"nombre": None})

    assert response.status_code == 422


def test_patch_unknown_returns_404(client: TestClient) -> None:
    assert client.patch("/autores/99", json={"nombre": "X"}).status_code == 404


def test_delete_removes_the_autor(client: TestClient, session: Session) -> None:
    autor = create_autor(session)

    assert client.delete(f"/autores/{autor.id}").status_code == 204
    assert client.get(f"/autores/{autor.id}").status_code == 404


def test_delete_unknown_returns_404(client: TestClient) -> None:
    assert client.delete("/autores/99").status_code == 404
