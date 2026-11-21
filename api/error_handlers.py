from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from exceptions import ConflictError, DomainError, ForbiddenError, NotFoundError

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotFoundError: 404,
    ForbiddenError: 403,
    ConflictError: 409,
}


def _build_handler(status_code: int):
    """Arma un handler que responde con `status_code` y el mensaje del error."""

    async def handler(_: Request, exc: Exception) -> JSONResponse:
        detail = exc.message if isinstance(exc, DomainError) else str(exc)
        return JSONResponse(status_code=status_code, content={"detail": detail})

    return handler


def register_error_handlers(app: FastAPI) -> None:
    # Starlette elige el handler según la jerarquía de clases: las subclases heredan el código
    for error_type, status_code in _STATUS_BY_ERROR.items():
        app.add_exception_handler(error_type, _build_handler(status_code))
