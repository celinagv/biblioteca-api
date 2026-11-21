import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.factories import create_libro, create_prestamo, create_socio

PAYLOAD = {"nombre": "Ana Pérez", "email": "ana@example.com"}


def test_create_returns_201_and_is_active_by_default(client: TestClient) -> None:
    response = client.post("/socios", json=PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {"id": 1, **PAYLOAD, "activo": True}


def test_create_normalizes_email_to_lowercase(client: TestClient) -> None:
    response = client.post("/socios", json={**PAYLOAD, "email": "ANA@Example.COM"})

    assert response.json()["email"] == "ana@example.com"


def test_create_rejects_duplicate_email_ignoring_case(client: TestClient) -> None:
    client.post("/socios", json=PAYLOAD)

    response = client.post("/socios", json={**PAYLOAD, "email": "Ana@Example.com"})

    assert response.status_code == 409
    assert response.json() == {"detail": "Ya existe un socio con el email ana@example.com"}


@pytest.mark.parametrize("email", ["no-es-un-email", "ana@", ""])
def test_create_rejects_invalid_email(client: TestClient, email: str) -> None:
    assert client.post("/socios", json={**PAYLOAD, "email": email}).status_code == 422


def test_get_and_404(client: TestClient, session: Session) -> None:
    socio = create_socio(session)

    assert client.get(f"/socios/{socio.id}").status_code == 200
    assert client.get("/socios/99").status_code == 404


def test_put_replaces_all_fields(client: TestClient, session: Session) -> None:
    socio = create_socio(session)
    body = {"nombre": "Nuevo", "email": "nuevo@example.com", "activo": False}

    response = client.put(f"/socios/{socio.id}", json=body)

    assert response.json() == {"id": socio.id, **body}


def test_put_requires_every_field(client: TestClient, session: Session) -> None:
    socio = create_socio(session)

    response = client.put(f"/socios/{socio.id}", json={"nombre": "X", "email": "x@example.com"})

    assert response.status_code == 422


def test_put_allows_keeping_own_email(client: TestClient, session: Session) -> None:
    socio = create_socio(session, email="mio@example.com")
    body = {"nombre": "Otro nombre", "email": "mio@example.com", "activo": True}

    assert client.put(f"/socios/{socio.id}", json=body).status_code == 200


def test_put_rejects_email_of_another_socio(client: TestClient, session: Session) -> None:
    create_socio(session, email="ocupado@example.com")
    socio = create_socio(session)
    body = {"nombre": "X", "email": "ocupado@example.com", "activo": True}

    assert client.put(f"/socios/{socio.id}", json=body).status_code == 409


def test_patch_changes_only_sent_fields(client: TestClient, session: Session) -> None:
    socio = create_socio(session, nombre="Ana", email="ana@example.com")

    response = client.patch(f"/socios/{socio.id}", json={"nombre": "Ana María"})

    assert response.json() == {
        "id": socio.id,
        "nombre": "Ana María",
        "email": "ana@example.com",
        "activo": True,
    }


def test_patch_rejects_email_of_another_socio(client: TestClient, session: Session) -> None:
    create_socio(session, email="ocupado@example.com")
    socio = create_socio(session)

    response = client.patch(f"/socios/{socio.id}", json={"email": "ocupado@example.com"})

    assert response.status_code == 409


def test_patch_rejects_explicit_null(client: TestClient, session: Session) -> None:
    socio = create_socio(session)

    assert client.patch(f"/socios/{socio.id}", json={"activo": None}).status_code == 422


def test_baja_marks_the_socio_inactive_and_is_idempotent(
    client: TestClient, session: Session
) -> None:
    socio = create_socio(session)

    first = client.post(f"/socios/{socio.id}/baja")
    second = client.post(f"/socios/{socio.id}/baja")

    assert first.status_code == second.status_code == 200
    assert first.json()["activo"] is False
    assert second.json()["activo"] is False


def test_baja_unknown_returns_404(client: TestClient) -> None:
    assert client.post("/socios/99/baja").status_code == 404


def test_delete_removes_a_socio_without_prestamos(client: TestClient, session: Session) -> None:
    socio = create_socio(session)

    assert client.delete(f"/socios/{socio.id}").status_code == 204
    assert client.get(f"/socios/{socio.id}").status_code == 404


def test_delete_with_prestamos_returns_409_and_keeps_the_socio(
    client: TestClient, session: Session
) -> None:
    socio = create_socio(session)
    create_prestamo(session, socio, create_libro(session))

    response = client.delete(f"/socios/{socio.id}")

    assert response.status_code == 409
    assert client.get(f"/socios/{socio.id}").json()["activo"] is True


def test_delete_unknown_returns_404(client: TestClient) -> None:
    assert client.delete("/socios/99").status_code == 404
