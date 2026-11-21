"""Tablas de la base de datos (SQLModel). Al importarlas acá quedan registradas en el metadata."""

from models.autor import Autor
from models.libro import Libro
from models.libro_autor import LibroAutor
from models.prestamo import Prestamo
from models.socio import Socio

__all__ = ["Autor", "Libro", "LibroAutor", "Prestamo", "Socio"]
