from sqlmodel import Field

from models.base import IdModel


class Socio(IdModel, table=True):
    """Persona registrada en la biblioteca que puede pedir libros prestados."""

    nombre: str = Field(max_length=100)
    email: str = Field(max_length=254, unique=True)
    activo: bool = True
