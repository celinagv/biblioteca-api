"""Pobla la base con datos de ejemplo. Se ejecuta con: python -m scripts.seed"""

from datetime import date, timedelta

from sqlmodel import Session

from api.schemas.autor import AutorCreate
from api.schemas.libro import LibroCreate
from api.schemas.prestamo import PrestamoCreate
from api.schemas.socio import SocioCreate
from config import get_settings
from database import create_db_and_tables, engine
from dependencies import (
    get_autor_service,
    get_libro_service,
    get_prestamo_service,
    get_socio_service,
)
from models.base import IdModel
from services.autores import AutorService
from services.libros import LibroService
from services.prestamos import PrestamoService
from services.socios import SocioService

AUTORES = {
    "borges": ("Jorge Luis Borges", "Argentina"),
    "bioy": ("Adolfo Bioy Casares", "Argentina"),
    "allende": ("Isabel Allende", "Chilena"),
    "storni": ("Alfonsina Storni", "Argentina"),
}

# Cada libro: (título, ISBN de ejemplo, stock, año, claves de sus autores en AUTORES)
LIBROS = [
    ("Ficciones", "9780000000011", 3, 1944, ["borges"]),
    ("La casa de los espíritus", "9780000000028", 2, 1982, ["allende"]),
    ("Languidez", "9780000000035", 1, 1920, ["storni"]),
    ("Seis problemas para don Isidro Parodi", "9780000000042", 0, 1942, ["borges", "bioy"]),
    ("El Aleph", "9780000000059", 2, 1949, ["borges"]),
]

# Cada socio: (nombre, email, activo)
SOCIOS = [
    ("Valentina Ríos", "valentina@example.com", True),
    ("Matías Ferreyra", "matias@example.com", True),
    ("Julieta Acosta", "julieta@example.com", True),
    ("Nicolás Benítez", "nicolas@example.com", False),
]

# Cada préstamo: (posición del socio, posición del libro, días desde que se prestó,
# días desde que se devolvió o None si sigue abierto)
# Cubre cuatro casos: uno reciente, uno vencido sin devolver, uno devuelto a tiempo y uno tardío
PRESTAMOS = [
    (0, 0, 3, None),
    (1, 1, 20, None),
    (0, 4, 30, 20),
    (2, 4, 40, 20),
]


def _pk(entity: IdModel) -> int:
    if entity.id is None:
        raise ValueError("La entidad aún no fue guardada en la base")
    return entity.id


def _load_autores(service: AutorService) -> dict[str, int]:
    return {
        clave: _pk(service.create(AutorCreate(nombre=nombre, nacionalidad=nacionalidad)))
        for clave, (nombre, nacionalidad) in AUTORES.items()
    }


def _load_libros(service: LibroService, autor_ids: dict[str, int]) -> list[int]:
    libro_ids = []
    for titulo, isbn, stock, anio, claves_autores in LIBROS:
        nuevo = service.create(LibroCreate(titulo=titulo, isbn=isbn, stock=stock, anio=anio))
        for clave in claves_autores:
            service.add_autor(_pk(nuevo), autor_ids[clave])
        libro_ids.append(_pk(nuevo))
    return libro_ids


def _load_socios(service: SocioService) -> list[int]:
    socio_ids = []
    for nombre, email, activo in SOCIOS:
        nuevo = service.create(SocioCreate(nombre=nombre, email=email))
        if not activo:
            service.deactivate(_pk(nuevo))
        socio_ids.append(_pk(nuevo))
    return socio_ids


def _load_prestamos(
    service: PrestamoService, socio_ids: list[int], libro_ids: list[int], today: date
) -> None:
    for pos_socio, pos_libro, borrowed_days_ago, returned_days_ago in PRESTAMOS:
        solicitud = PrestamoCreate(socio_id=socio_ids[pos_socio], libro_id=libro_ids[pos_libro])
        creado = service.create(solicitud, today - timedelta(days=borrowed_days_ago))
        if returned_days_ago is not None:
            service.return_loan(_pk(creado), today - timedelta(days=returned_days_ago))


def seed(session: Session, today: date) -> bool:
    """Inserta el conjunto de ejemplo a través de los servicios, para que rijan las reglas.

    Si la base ya contiene datos no modifica nada y devuelve False.
    """
    autor_service = get_autor_service(session)
    if autor_service.list(limit=1, offset=0):
        return False

    autor_ids = _load_autores(autor_service)
    libro_ids = _load_libros(get_libro_service(session), autor_ids)
    socio_ids = _load_socios(get_socio_service(session))
    _load_prestamos(get_prestamo_service(session, get_settings()), socio_ids, libro_ids, today)
    return True


def main() -> None:
    create_db_and_tables()
    with Session(engine) as session:
        loaded = seed(session, date.today())
    print("Datos de ejemplo cargados." if loaded else "La base ya tiene datos; no se agregó nada.")


if __name__ == "__main__":
    main()
