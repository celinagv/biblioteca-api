"""Tipos anotados reutilizables que ya traen incorporadas sus validaciones."""

import re
from datetime import date
from typing import Annotated

from fastapi import Path
from pydantic import AfterValidator, EmailStr, Field, StringConstraints

MAX_INT = 2**63 - 1  # tope de un entero con signo de 64 bits, el máximo que acepta SQLite
MAX_STOCK = 1_000_000  # cota razonable para evitar cargas absurdas

_ISBN_PATTERN = re.compile(r"\d{9}[\dX]|\d{13}")


def _normalize_isbn(value: str) -> str:
    # Se almacena sin guiones ni espacios: "978-0-306..." y "9780306..." son el mismo ISBN
    compact = value.replace("-", "").replace(" ", "").upper()
    if not _ISBN_PATTERN.fullmatch(compact):
        raise ValueError("ISBN inválido: se esperan 10 o 13 dígitos")
    return compact


def _not_future(year: int) -> int:
    if year > date.today().year:
        raise ValueError("el año no puede ser posterior al actual")
    return year


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Nationality = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Isbn = Annotated[str, AfterValidator(_normalize_isbn)]
Year = Annotated[int, Field(ge=1), AfterValidator(_not_future)]
Stock = Annotated[int, Field(ge=0, le=MAX_STOCK)]
Email = Annotated[EmailStr, AfterValidator(str.lower)]
IdField = Annotated[int, Field(ge=1, le=MAX_INT)]
EntityId = Annotated[int, Path(ge=1, le=MAX_INT)]
