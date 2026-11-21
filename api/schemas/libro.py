from pydantic import BaseModel, ConfigDict

from api.schemas.autor import AutorRead
from api.schemas.base import PatchSchema, ReadSchema
from api.schemas.types import Isbn, Stock, Title, Year


class LibroReplace(BaseModel):
    """PUT: reemplazo completo, por lo que se exigen todos los campos."""

    titulo: Title
    isbn: Isbn
    stock: Stock
    anio: Year


class LibroCreate(LibroReplace):
    stock: Stock = 0

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "titulo": "Ficciones",
                    "isbn": "978-0-8021-3030-3",
                    "stock": 5,
                    "anio": 1944,
                }
            ]
        }
    )


class LibroPatch(PatchSchema):
    titulo: Title | None = None
    isbn: Isbn | None = None
    stock: Stock | None = None
    anio: Year | None = None

    model_config = ConfigDict(json_schema_extra={"examples": [{"stock": 8}]})


class LibroRead(ReadSchema):
    id: int
    titulo: str
    isbn: str
    stock: int
    anio: int
    autores: list[AutorRead]
