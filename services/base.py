from collections.abc import Sequence
from typing import Any, Generic

from pydantic import BaseModel

from api.schemas.base import PatchSchema
from exceptions import EntityNotFoundError
from repositories.base import BaseRepository, ModelT


class CrudService(Generic[ModelT]):
    """CRUD genérico. Las subclases suman reglas redefiniendo los hooks `_check_*`."""

    entity_name: str

    def __init__(self, repository: BaseRepository[ModelT]) -> None:
        self._repo = repository

    def get(self, entity_id: int) -> ModelT:
        record = self._repo.get(entity_id)
        if record is None:
            raise EntityNotFoundError(self.entity_name, entity_id)
        return record

    def list(self, *, limit: int, offset: int) -> Sequence[ModelT]:
        return self._repo.find_all(limit=limit, offset=offset)

    def create(self, data: BaseModel) -> ModelT:
        payload = data.model_dump()
        self._check_unique(payload, current_id=None)
        return self._repo.save(self._repo.model(**payload))

    def replace(self, entity_id: int, data: BaseModel) -> ModelT:
        record = self.get(entity_id)
        payload = data.model_dump()
        self._check_unique(payload, current_id=entity_id)
        return self._update(record, payload)

    def patch(self, entity_id: int, data: PatchSchema) -> ModelT:
        record = self.get(entity_id)
        partial = data.changes()
        self._check_unique(partial, current_id=entity_id)
        return self._update(record, partial)

    def delete(self, entity_id: int) -> None:
        record = self.get(entity_id)
        self._check_deletable(entity_id)
        self._repo.delete(record)

    def _update(self, entity: ModelT, values: dict[str, Any]) -> ModelT:
        entity.sqlmodel_update(values)
        return self._repo.save(entity)

    def _check_unique(self, values: dict[str, Any], current_id: int | None) -> None:
        """Hook: lanza ConflictError si algún valor repite un campo único de otro registro."""

    def _check_deletable(self, entity_id: int) -> None:
        """Hook: debe lanzar ConflictError si el registro no se puede eliminar."""
