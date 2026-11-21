from fastapi.testclient import TestClient
from sqlmodel import Session

from tests.factories import (
    create_autor,
    create_libro,
    create_prestamo,
    create_socio,
    link_autor,
)


def _autores_of(client: TestClient, libro_id: int | None) -> list[str]:
    return [a["nombre"] for a in client.get(f"/libros/{libro_id}").json()["autores"]]


def test_add_autor_returns_201_with_the_libro_and_its_autores(
    client: TestClient, session: Session
) -> None:
    libro = create_libro(session)
    autor = create_autor(session, nombre="Borges", nacionalidad="Argentina")

    response = client.post(f"/libros/{libro.id}/autores/{autor.id}")

    assert response.status_code == 201
    assert response.json()["id"] == libro.id
    assert response.json()["autores"] == [
        {"id": autor.id, "nombre": "Borges", "nacionalidad": "Argentina"}
    ]


def test_a_libro_can_have_several_autores_ordered_by_id(
    client: TestClient, session: Session
) -> None:
    libro = create_libro(session)
    primero = create_autor(session, nombre="Primero")
    segundo = create_autor(session, nombre="Segundo")

    client.post(f"/libros/{libro.id}/autores/{segundo.id}")
    client.post(f"/libros/{libro.id}/autores/{primero.id}")

    assert _autores_of(client, libro.id) == ["Primero", "Segundo"]


def test_an_autor_can_have_several_libros(client: TestClient, session: Session) -> None:
    autor = create_autor(session)
    libros = [create_libro(session) for _ in range(2)]

    for libro in libros:
        assert client.post(f"/libros/{libro.id}/autores/{autor.id}").status_code == 201


def test_add_autor_twice_returns_409(client: TestClient, session: Session) -> None:
    libro, autor = create_libro(session), create_autor(session)
    client.post(f"/libros/{libro.id}/autores/{autor.id}")

    response = client.post(f"/libros/{libro.id}/autores/{autor.id}")

    assert response.status_code == 409
    assert response.json() == {
        "detail": f"El autor {autor.id} ya está asociado al libro {libro.id}"
    }


def test_add_autor_to_unknown_libro_returns_404(client: TestClient, session: Session) -> None:
    autor = create_autor(session)

    response = client.post(f"/libros/99/autores/{autor.id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Libro con id 99 no encontrado"}


def test_add_unknown_autor_returns_404(client: TestClient, session: Session) -> None:
    libro = create_libro(session)

    response = client.post(f"/libros/{libro.id}/autores/99")

    assert response.status_code == 404
    assert response.json() == {"detail": "Autor con id 99 no encontrado"}


def test_get_and_list_include_the_autores(client: TestClient, session: Session) -> None:
    libro, autor = create_libro(session), create_autor(session, nombre="Ana")
    link_autor(session, libro, autor)
    create_libro(session)

    listing = client.get("/libros").json()

    assert [a["nombre"] for a in listing[0]["autores"]] == ["Ana"]
    assert listing[1]["autores"] == []
    assert _autores_of(client, libro.id) == ["Ana"]


def test_put_and_patch_keep_the_autores(client: TestClient, session: Session) -> None:
    libro, autor = create_libro(session), create_autor(session, nombre="Ana")
    link_autor(session, libro, autor)

    patched = client.patch(f"/libros/{libro.id}", json={"stock": 9})

    assert [a["nombre"] for a in patched.json()["autores"]] == ["Ana"]


def test_remove_autor_deletes_only_the_association(client: TestClient, session: Session) -> None:
    libro, autor = create_libro(session), create_autor(session)
    link_autor(session, libro, autor)

    response = client.delete(f"/libros/{libro.id}/autores/{autor.id}")

    assert response.status_code == 204
    assert _autores_of(client, libro.id) == []
    assert client.get(f"/autores/{autor.id}").status_code == 200


def test_remove_autor_not_associated_returns_404(client: TestClient, session: Session) -> None:
    libro, autor = create_libro(session), create_autor(session)

    response = client.delete(f"/libros/{libro.id}/autores/{autor.id}")

    assert response.status_code == 404
    assert response.json() == {
        "detail": f"El autor {autor.id} no está asociado al libro {libro.id}"
    }


def test_remove_autor_with_unknown_libro_or_autor_returns_404(
    client: TestClient, session: Session
) -> None:
    libro, autor = create_libro(session), create_autor(session)

    assert client.delete(f"/libros/99/autores/{autor.id}").status_code == 404
    assert client.delete(f"/libros/{libro.id}/autores/99").status_code == 404


def test_remove_autor_is_allowed_even_if_the_libro_has_prestamos(
    client: TestClient, session: Session
) -> None:
    libro, autor = create_libro(session), create_autor(session)
    link_autor(session, libro, autor)
    create_prestamo(session, create_socio(session), libro)

    assert client.delete(f"/libros/{libro.id}/autores/{autor.id}").status_code == 204


def test_deleting_an_autor_removes_its_associations_but_keeps_the_libros(
    client: TestClient, session: Session
) -> None:
    libro, autor = create_libro(session), create_autor(session)
    link_autor(session, libro, autor)

    assert client.delete(f"/autores/{autor.id}").status_code == 204

    assert client.get(f"/libros/{libro.id}").status_code == 200
    assert _autores_of(client, libro.id) == []


def test_deleting_a_libro_removes_its_associations_but_keeps_the_autores(
    client: TestClient, session: Session
) -> None:
    libro, autor = create_libro(session), create_autor(session)
    link_autor(session, libro, autor)

    assert client.delete(f"/libros/{libro.id}").status_code == 204

    assert client.get(f"/autores/{autor.id}").status_code == 200
    other = create_libro(session)
    assert client.post(f"/libros/{other.id}/autores/{autor.id}").status_code == 201


def test_libro_with_prestamos_keeps_its_associations_when_delete_is_rejected(
    client: TestClient, session: Session
) -> None:
    libro, autor = create_libro(session), create_autor(session, nombre="Ana")
    link_autor(session, libro, autor)
    create_prestamo(session, create_socio(session), libro)

    assert client.delete(f"/libros/{libro.id}").status_code == 409
    assert _autores_of(client, libro.id) == ["Ana"]
