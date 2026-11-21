from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship

from models.base import IdModel
from models.libro_autor import LibroAutor

if TYPE_CHECKING:
    from models.autor import Autor


class Libro(IdModel, table=True):
    """Título del catálogo, con su stock de ejemplares disponibles."""

    __table_args__ = (CheckConstraint("stock >= 0", name="ck_libro_stock_no_negativo"),)

    titulo: str = Field(max_length=200)
    isbn: str = Field(max_length=13, unique=True)
    stock: int = 0
    anio: int

    autores: list["Autor"] = Relationship(
        back_populates="libros",
        link_model=LibroAutor,
        sa_relationship_kwargs={"order_by": "Autor.id"},
    )
