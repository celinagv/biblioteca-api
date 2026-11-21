from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from exceptions import ConflictError
from models.base import IdModel

ModelT = TypeVar("ModelT", bound=IdModel)


class BaseRepository(Generic[ModelT]):
    """Acceso a datos genérico. Cada subclase indica con `model` qué tabla administra."""

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, entity_id: int) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def find_all(self, *, limit: int, offset: int) -> Sequence[ModelT]:
        # Se ordena por id: sin un orden fijo la paginación podría repetir o saltear filas
        sentencia = select(self.model).order_by(col(self.model.id)).offset(offset).limit(limit)
        return self.session.exec(sentencia).all()

    def add(self, entity: ModelT) -> None:
        """Deja la entidad en la sesión sin confirmar; sirve para operaciones de varios pasos."""
        self.session.add(entity)

    def save(self, entity: ModelT) -> ModelT:
        self.add(entity)
        self.commit()
        self.session.refresh(entity)
        return entity

    def refresh(self, entity: ModelT) -> None:
        self.session.refresh(entity)

    def delete(self, entity: ModelT) -> None:
        self.session.delete(entity)
        self.commit()

    def commit(self) -> None:
        # Última defensa ante carreras: si la base rechaza algo que las validaciones no vieron
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("No se pudo guardar: se violó una restricción de datos") from exc
