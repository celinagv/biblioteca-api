"""Creación de datos de prueba directamente en la base."""

from datetime import date
from itertools import count
from typing import Any, TypeVar

from sqlmodel import Session

from models import Autor, Libro, Prestamo, Socio
from models.base import IdModel

_sequence = count(1)
ModelT = TypeVar("ModelT", bound=IdModel)


def _save(session: Session, entity: ModelT) -> ModelT:
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return entity


def create_autor(session: Session, **overrides: Any) -> Autor:
    n = next(_sequence)
    data = {"nombre": f"Autor {n}", "nacionalidad": "Argentina", **overrides}
    return _save(session, Autor(**data))


def create_socio(session: Session, **overrides: Any) -> Socio:
    n = next(_sequence)
    data = {"nombre": f"Socio {n}", "email": f"socio{n}@example.com", "activo": True, **overrides}
    return _save(session, Socio(**data))


def create_libro(session: Session, **overrides: Any) -> Libro:
    n = next(_sequence)
    data = {
        "titulo": f"Libro {n}",
        "isbn": str(9780000000000 + n),
        "stock": 1,
        "anio": 2000,
        **overrides,
    }
    return _save(session, Libro(**data))


def create_prestamo(session: Session, socio: Socio, libro: Libro, **overrides: Any) -> Prestamo:
    data = {
        "socio_id": socio.id,
        "libro_id": libro.id,
        "fecha_prestamo": date(2026, 1, 1),
        "fecha_vencimiento": date(2026, 1, 15),
        **overrides,
    }
    return _save(session, Prestamo(**data))


def link_autor(session: Session, libro: Libro, autor: Autor) -> None:
    libro.autores.append(autor)
    session.commit()
