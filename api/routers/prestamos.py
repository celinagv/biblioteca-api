from fastapi import APIRouter, status

from api.schemas.errors import CONFLICT, FORBIDDEN, NOT_FOUND
from api.schemas.prestamo import PrestamoCreate, PrestamoRead
from api.schemas.types import EntityId
from dependencies import PrestamoServiceDep, TodayDep
from models.prestamo import Prestamo

router = APIRouter(prefix="/prestamos", tags=["Préstamos"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PrestamoRead,
    responses={**FORBIDDEN, **NOT_FOUND, **CONFLICT},
)
def create_prestamo(data: PrestamoCreate, service: PrestamoServiceDep, today: TodayDep) -> Prestamo:
    """Registra un préstamo: descuenta 1 de stock y fija el vencimiento según el plazo."""
    return service.create(data, today)


@router.get("/{prestamo_id}", response_model=PrestamoRead, responses=NOT_FOUND)
def get_prestamo(prestamo_id: EntityId, service: PrestamoServiceDep) -> Prestamo:
    return service.get(prestamo_id)


@router.post(
    "/{prestamo_id}/devolucion",
    response_model=PrestamoRead,
    responses={**NOT_FOUND, **CONFLICT},
)
def return_prestamo(
    prestamo_id: EntityId, service: PrestamoServiceDep, today: TodayDep
) -> Prestamo:
    """Registra la devolución: reintegra el stock y calcula la multa si hubo atraso."""
    return service.return_loan(prestamo_id, today)
