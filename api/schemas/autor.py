from pydantic import BaseModel, ConfigDict

from api.schemas.base import PatchSchema, ReadSchema
from api.schemas.types import Name, Nationality


class AutorCreate(BaseModel):
    nombre: Name
    nacionalidad: Nationality

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"nombre": "Julio Cortázar", "nacionalidad": "Argentina"}]}
    )


class AutorReplace(AutorCreate):
    """PUT: reemplazo completo, con los mismos campos (todos obligatorios) que el alta."""


class AutorPatch(PatchSchema):
    nombre: Name | None = None
    nacionalidad: Nationality | None = None

    model_config = ConfigDict(json_schema_extra={"examples": [{"nacionalidad": "Uruguaya"}]})


class AutorRead(ReadSchema):
    id: int
    nombre: str
    nacionalidad: str
