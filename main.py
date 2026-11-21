from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.error_handlers import register_error_handlers
from api.routers import autores, health, libros, prestamos, socios
from database import create_db_and_tables


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Al iniciar el servidor se crean las tablas que todavía no existan
    create_db_and_tables()
    yield


TAGS_METADATA = [
    {"name": "Autores", "description": "Alta, consulta y mantenimiento de autores."},
    {"name": "Libros", "description": "Catálogo de libros: stock y autores asociados."},
    {"name": "Socios", "description": "Socios de la biblioteca y el historial de sus préstamos."},
    {"name": "Préstamos", "description": "Registro de préstamos y de sus devoluciones."},
    {"name": "Health", "description": "Chequeo de disponibilidad del servicio."},
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="API de Gestión de Biblioteca",
        description="Libros, autores, socios y préstamos, con control de stock y multas.",
        version="0.1.0",
        openapi_tags=TAGS_METADATA,
        lifespan=lifespan,
    )
    register_error_handlers(app)
    # Un router por recurso; el orden de registro solo afecta cómo se ve la documentación
    app.include_router(health.router)
    app.include_router(autores.router)
    app.include_router(libros.router)
    app.include_router(socios.router)
    app.include_router(prestamos.router)
    return app


app = create_app()
