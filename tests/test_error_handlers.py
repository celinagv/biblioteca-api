import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.error_handlers import register_error_handlers
from exceptions import (
    ConflictError,
    DomainError,
    EntityNotFoundError,
    ForbiddenError,
    NotFoundError,
)


class StockAgotadoError(ConflictError):
    """Subclase de ejemplo: debe heredar el 409."""


def _raiser(error: DomainError):
    def endpoint() -> None:
        raise error

    return endpoint


@pytest.fixture
def error_client() -> TestClient:
    app = FastAPI()
    register_error_handlers(app)
    app.add_api_route("/not-found", _raiser(EntityNotFoundError("Libro", 7)))
    app.add_api_route("/missing", _raiser(NotFoundError("No hay nada")))
    app.add_api_route("/forbidden", _raiser(ForbiddenError("Socio inactivo")))
    app.add_api_route("/conflict", _raiser(ConflictError("ISBN duplicado")))
    app.add_api_route("/subclass", _raiser(StockAgotadoError("Sin stock")))
    return TestClient(app)


@pytest.mark.parametrize(
    ("path", "status_code", "detail"),
    [
        ("/not-found", 404, "Libro con id 7 no encontrado"),
        ("/missing", 404, "No hay nada"),
        ("/forbidden", 403, "Socio inactivo"),
        ("/conflict", 409, "ISBN duplicado"),
        ("/subclass", 409, "Sin stock"),
    ],
)
def test_domain_errors_become_http_errors(
    error_client: TestClient, path: str, status_code: int, detail: str
) -> None:
    response = error_client.get(path)

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}
