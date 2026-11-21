from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from models.base import IdModel
from models.libro_autor import LibroAutor

if TYPE_CHECKING:
    from models.libro import Libro


class Autor(IdModel, table=True):
    """Persona que escribió uno o más libros del catálogo."""

    nombre: str = Field(max_length=100)
    nacionalidad: str = Field(max_length=60)

    libros: list["Libro"] = Relationship(back_populates="autores", link_model=LibroAutor)
