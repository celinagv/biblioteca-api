from dataclasses import dataclass
from datetime import date
from typing import Annotated

from fastapi import Depends, Query
from sqlmodel import Session

from api.schemas.types import MAX_INT
from config import Settings, get_settings
from database import get_session
from repositories.autores import AutorRepository
from repositories.libros import LibroRepository
from repositories.prestamos import PrestamoRepository
from repositories.socios import SocioRepository
from services.autores import AutorService
from services.libros import LibroService
from services.prestamos import PrestamoService
from services.socios import SocioService

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_today() -> date:
    """Fecha de hoy como dependencia: los tests la reemplazan para simular atrasos."""
    return date.today()


TodayDep = Annotated[date, Depends(get_today)]


@dataclass
class Pagination:
    """Parámetros de paginación que comparten todos los listados."""

    limit: Annotated[int, Query(ge=1, le=100, description="Cantidad máxima de resultados")] = 20
    offset: Annotated[int, Query(ge=0, le=MAX_INT, description="Registros a omitir")] = 0


PaginationDep = Annotated[Pagination, Depends()]


# Fábricas de servicios: cada una arma el servicio con los repositorios que necesita
def get_autor_service(session: SessionDep) -> AutorService:
    return AutorService(AutorRepository(session))


def get_socio_service(session: SessionDep) -> SocioService:
    return SocioService(SocioRepository(session), PrestamoRepository(session))


def get_libro_service(session: SessionDep) -> LibroService:
    return LibroService(
        LibroRepository(session), AutorRepository(session), PrestamoRepository(session)
    )


# Alias para inyectar los servicios directamente en la firma de los endpoints
AutorServiceDep = Annotated[AutorService, Depends(get_autor_service)]
SocioServiceDep = Annotated[SocioService, Depends(get_socio_service)]
LibroServiceDep = Annotated[LibroService, Depends(get_libro_service)]


def get_prestamo_service(session: SessionDep, settings: SettingsDep) -> PrestamoService:
    # Es el único servicio que además necesita la configuración (plazo, multa y tope)
    return PrestamoService(
        PrestamoRepository(session),
        SocioRepository(session),
        LibroRepository(session),
        settings,
    )


PrestamoServiceDep = Annotated[PrestamoService, Depends(get_prestamo_service)]
