from typing import Annotated

from fastapi import APIRouter, Query, status

from api.schemas.errors import CONFLICT, NOT_FOUND
from api.schemas.libro import LibroCreate, LibroPatch, LibroRead, LibroReplace
from api.schemas.types import EntityId
from dependencies import LibroServiceDep, PaginationDep
from models.libro import Libro

router = APIRouter(prefix="/libros", tags=["Libros"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LibroRead, responses=CONFLICT)
def create_libro(data: LibroCreate, service: LibroServiceDep) -> Libro:
    return service.create(data)


@router.get("", response_model=list[LibroRead])
def list_libros(
    page: PaginationDep,
    service: LibroServiceDep,
    disponibles: Annotated[
        bool | None, Query(description="true: solo con stock; false: sin stock; omitido: todos")
    ] = None,
) -> list[Libro]:
    return list(service.list(limit=page.limit, offset=page.offset, disponibles=disponibles))


@router.get("/{libro_id}", response_model=LibroRead, responses=NOT_FOUND)
def get_libro(libro_id: EntityId, service: LibroServiceDep) -> Libro:
    return service.get(libro_id)


@router.put("/{libro_id}", response_model=LibroRead, responses={**NOT_FOUND, **CONFLICT})
def replace_libro(libro_id: EntityId, data: LibroReplace, service: LibroServiceDep) -> Libro:
    return service.replace(libro_id, data)


@router.patch("/{libro_id}", response_model=LibroRead, responses={**NOT_FOUND, **CONFLICT})
def patch_libro(libro_id: EntityId, data: LibroPatch, service: LibroServiceDep) -> Libro:
    return service.patch(libro_id, data)


@router.delete(
    "/{libro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**NOT_FOUND, **CONFLICT},
)
def delete_libro(libro_id: EntityId, service: LibroServiceDep) -> None:
    """Elimina el libro. Responde 409 si ya tiene préstamos registrados."""
    service.delete(libro_id)


@router.post(
    "/{libro_id}/autores/{autor_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=LibroRead,
    responses={**NOT_FOUND, **CONFLICT},
)
def add_autor(libro_id: EntityId, autor_id: EntityId, service: LibroServiceDep) -> Libro:
    """Vincula un autor existente con el libro."""
    return service.add_autor(libro_id, autor_id)


@router.delete(
    "/{libro_id}/autores/{autor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def remove_autor(libro_id: EntityId, autor_id: EntityId, service: LibroServiceDep) -> None:
    """Desvincula al autor del libro; ni el libro ni el autor se eliminan."""
    service.remove_autor(libro_id, autor_id)
