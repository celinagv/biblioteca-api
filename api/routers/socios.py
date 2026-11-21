from typing import Annotated

from fastapi import APIRouter, Query, status

from api.schemas.errors import CONFLICT, NOT_FOUND
from api.schemas.prestamo import PrestamoRead
from api.schemas.socio import SocioCreate, SocioPatch, SocioRead, SocioReplace
from api.schemas.types import EntityId
from dependencies import PaginationDep, PrestamoServiceDep, SocioServiceDep
from models.prestamo import Prestamo
from models.socio import Socio

router = APIRouter(prefix="/socios", tags=["Socios"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SocioRead, responses=CONFLICT)
def create_socio(data: SocioCreate, service: SocioServiceDep) -> Socio:
    return service.create(data)


@router.get("", response_model=list[SocioRead])
def list_socios(page: PaginationDep, service: SocioServiceDep) -> list[Socio]:
    return list(service.list(limit=page.limit, offset=page.offset))


@router.get("/{socio_id}", response_model=SocioRead, responses=NOT_FOUND)
def get_socio(socio_id: EntityId, service: SocioServiceDep) -> Socio:
    return service.get(socio_id)


@router.put("/{socio_id}", response_model=SocioRead, responses={**NOT_FOUND, **CONFLICT})
def replace_socio(socio_id: EntityId, data: SocioReplace, service: SocioServiceDep) -> Socio:
    return service.replace(socio_id, data)


@router.patch("/{socio_id}", response_model=SocioRead, responses={**NOT_FOUND, **CONFLICT})
def patch_socio(socio_id: EntityId, data: SocioPatch, service: SocioServiceDep) -> Socio:
    return service.patch(socio_id, data)


@router.post("/{socio_id}/baja", response_model=SocioRead, responses=NOT_FOUND)
def deactivate_socio(socio_id: EntityId, service: SocioServiceDep) -> Socio:
    """Da de baja al socio (activo = false) conservando su historial."""
    return service.deactivate(socio_id)


@router.delete(
    "/{socio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**NOT_FOUND, **CONFLICT},
)
def delete_socio(socio_id: EntityId, service: SocioServiceDep) -> None:
    """Elimina al socio. Con préstamos registrados responde 409; en ese caso, darlo de baja."""
    service.delete(socio_id)


@router.get("/{socio_id}/prestamos", response_model=list[PrestamoRead], responses=NOT_FOUND)
def list_socio_prestamos(
    socio_id: EntityId,
    page: PaginationDep,
    service: PrestamoServiceDep,
    activos: Annotated[
        bool | None, Query(description="true: sin devolver aún; false: devueltos; omitido: todos")
    ] = None,
) -> list[Prestamo]:
    """Lista los préstamos del socio; con `activos` se filtra por estado."""
    return list(
        service.list_by_socio(socio_id, activos=activos, limit=page.limit, offset=page.offset)
    )
