from datetime import date

from sqlmodel import Field

from models.base import IdModel


class Prestamo(IdModel, table=True):
    """Préstamo de un libro a un socio; sin fecha de devolución sigue pendiente."""

    socio_id: int = Field(foreign_key="socio.id", index=True)
    libro_id: int = Field(foreign_key="libro.id", index=True)
    fecha_prestamo: date
    fecha_vencimiento: date
    fecha_devolucion: date | None = None
    multa: int = 0
