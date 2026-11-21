from collections.abc import Sequence
from typing import Any, cast

from sqlalchemy import update
from sqlalchemy.orm import QueryableAttribute, selectinload
from sqlmodel import col, select

from models.libro import Libro
from repositories.base import BaseRepository

# Trae los autores de todos los libros en una única sentencia extra (evita el problema N+1)
_AUTORES = cast("QueryableAttribute[Any]", Libro.autores)


class LibroRepository(BaseRepository[Libro]):
    model = Libro

    def get(self, entity_id: int) -> Libro | None:
        return self.session.get(Libro, entity_id, options=[selectinload(_AUTORES)])

    def find_all(
        self, *, limit: int, offset: int, disponibles: bool | None = None
    ) -> Sequence[Libro]:
        sentencia = select(Libro).options(selectinload(_AUTORES))
        if disponibles is not None:
            stock_col = col(Libro.stock)
            sentencia = sentencia.where(stock_col > 0 if disponibles else stock_col == 0)
        sentencia = sentencia.order_by(col(Libro.id)).offset(offset).limit(limit)
        return self.session.exec(sentencia).all()

    def get_by_isbn(self, isbn: str) -> Libro | None:
        sentencia = select(Libro).where(col(Libro.isbn) == isbn)
        return self.session.exec(sentencia).first()

    def take_one_from_stock(self, libro_id: int) -> bool:
        """Resta 1 al stock con una sola sentencia. Devuelve False si no quedaban ejemplares."""
        # La condición stock > 0 del WHERE impide que dos préstamos simultáneos tomen la última
        sentencia = (
            update(Libro)
            .where(col(Libro.id) == libro_id, col(Libro.stock) > 0)
            .values(stock=col(Libro.stock) - 1)
        )
        return self.session.connection().execute(sentencia).rowcount == 1

    def return_one_to_stock(self, libro_id: int) -> None:
        """Suma 1 al stock (el ejemplar volvió a la biblioteca)."""
        sentencia = (
            update(Libro).where(col(Libro.id) == libro_id).values(stock=col(Libro.stock) + 1)
        )
        self.session.connection().execute(sentencia)
