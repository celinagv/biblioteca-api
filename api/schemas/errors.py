from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    detail: str


Responses = dict[int | str, dict[str, Any]]

FORBIDDEN: Responses = {403: {"model": ErrorResponse, "description": "Acción no permitida"}}
NOT_FOUND: Responses = {404: {"model": ErrorResponse, "description": "El recurso no existe"}}
CONFLICT: Responses = {
    409: {"model": ErrorResponse, "description": "Conflicto con el estado actual del recurso"}
}
