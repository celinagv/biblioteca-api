from collections.abc import Sequence
from typing import Any

from exceptions import ConflictError, EntityNotFoundError, NotFoundError
from models.libro import Libro
from repositories.autores import AutorRepository
from repositories.libros import LibroRepository
from repositories.prestamos import PrestamoRepository
from services.base import CrudService


class LibroService(CrudService[Libro]):
    """CRUD de libros más la gestión de sus autores y las reglas de unicidad y borrado."""

    entity_name = "Libro"

    def __init__(
        self,
        libros: LibroRepository,
        autores: AutorRepository,
        prestamos: PrestamoRepository,
    ) -> None:
        super().__init__(libros)
        self._libros = libros
        self._autores = autores
        self._prestamos = prestamos

    def list(self, *, limit: int, offset: int, disponibles: bool | None = None) -> Sequence[Libro]:
        return self._libros.find_all(limit=limit, offset=offset, disponibles=disponibles)

    def add_autor(self, libro_id: int, autor_id: int) -> Libro:
        """Vincula el autor con el libro; responde 409 si ya estaban vinculados."""
        libro = self.get(libro_id)
        autor = self._get_autor(autor_id)
        if autor in libro.autores:
            raise ConflictError(f"El autor {autor_id} ya está asociado al libro {libro_id}")
        libro.autores.append(autor)
        self._libros.commit()
        self._libros.refresh(libro)
        return libro

    def remove_autor(self, libro_id: int, autor_id: int) -> None:
        """Desvincula el autor del libro; responde 404 si no estaban vinculados."""
        libro = self.get(libro_id)
        autor = self._get_autor(autor_id)
        if autor not in libro.autores:
            raise NotFoundError(f"El autor {autor_id} no está asociado al libro {libro_id}")
        libro.autores.remove(autor)
        self._libros.commit()

    def _get_autor(self, autor_id: int):
        autor = self._autores.get(autor_id)
        if autor is None:
            raise EntityNotFoundError("Autor", autor_id)
        return autor

    def _check_unique(self, values: dict[str, Any], current_id: int | None) -> None:
        isbn_recibido = values.get("isbn")
        if isbn_recibido is None:
            return
        duplicado = self._libros.get_by_isbn(isbn_recibido)
        if duplicado is not None and duplicado.id != current_id:
            raise ConflictError(f"Ya existe un libro con el ISBN {isbn_recibido}")

    def _check_deletable(self, entity_id: int) -> None:
        if self._prestamos.exists_for_libro(entity_id):
            raise ConflictError("No se puede eliminar el libro porque tiene préstamos registrados")
