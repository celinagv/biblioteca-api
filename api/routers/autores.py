from fastapi import APIRouter, status

from api.schemas.autor import AutorCreate, AutorPatch, AutorRead, AutorReplace
from api.schemas.errors import NOT_FOUND
from api.schemas.types import EntityId
from dependencies import AutorServiceDep, PaginationDep
from models.autor import Autor

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AutorRead)
def create_autor(data: AutorCreate, service: AutorServiceDep) -> Autor:
    """Da de alta un autor nuevo."""
    return service.create(data)


@router.get("", response_model=list[AutorRead])
def list_autores(page: PaginationDep, service: AutorServiceDep) -> list[Autor]:
    """Lista los autores, paginados y ordenados por id."""
    return list(service.list(limit=page.limit, offset=page.offset))


@router.get("/{autor_id}", response_model=AutorRead, responses=NOT_FOUND)
def get_autor(autor_id: EntityId, service: AutorServiceDep) -> Autor:
    """Devuelve un autor por su id."""
    return service.get(autor_id)


@router.put("/{autor_id}", response_model=AutorRead, responses=NOT_FOUND)
def replace_autor(autor_id: EntityId, data: AutorReplace, service: AutorServiceDep) -> Autor:
    """Reemplaza todos los datos del autor (PUT)."""
    return service.replace(autor_id, data)


@router.patch("/{autor_id}", response_model=AutorRead, responses=NOT_FOUND)
def patch_autor(autor_id: EntityId, data: AutorPatch, service: AutorServiceDep) -> Autor:
    """Modifica solo los campos enviados del autor (PATCH)."""
    return service.patch(autor_id, data)


@router.delete("/{autor_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_autor(autor_id: EntityId, service: AutorServiceDep) -> None:
    """Elimina al autor."""
    service.delete(autor_id)
