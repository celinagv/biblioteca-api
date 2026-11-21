from pydantic import BaseModel, ConfigDict

from api.schemas.base import PatchSchema, ReadSchema
from api.schemas.types import Email, Name


class SocioReplace(BaseModel):
    """PUT: reemplazo completo, por lo que se exigen todos los campos."""

    nombre: Name
    email: Email
    activo: bool


class SocioCreate(SocioReplace):
    activo: bool = True

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"nombre": "Lucía Gil", "email": "lucia@example.com"}]}
    )


class SocioPatch(PatchSchema):
    nombre: Name | None = None
    email: Email | None = None
    activo: bool | None = None

    model_config = ConfigDict(json_schema_extra={"examples": [{"nombre": "Lucía Inés Gil"}]})


class SocioRead(ReadSchema):
    id: int
    nombre: str
    email: str
    activo: bool
