from collections.abc import Sequence
from datetime import date

from sqlalchemy import func, update
from sqlmodel import col, select

from models.prestamo import Prestamo
from repositories.base import BaseRepository


class PrestamoRepository(BaseRepository[Prestamo]):
    model = Prestamo

    def exists_for_socio(self, socio_id: int) -> bool:
        """Indica si el socio tiene algún préstamo, devuelto o no."""
        sentencia = select(col(Prestamo.id)).where(col(Prestamo.socio_id) == socio_id).limit(1)
        return self.session.exec(sentencia).first() is not None

    def exists_for_libro(self, libro_id: int) -> bool:
        """Indica si el libro figura en algún préstamo, devuelto o no."""
        sentencia = select(col(Prestamo.id)).where(col(Prestamo.libro_id) == libro_id).limit(1)
        return self.session.exec(sentencia).first() is not None

    def count_active_by_socio(self, socio_id: int) -> int:
        """Cuenta los préstamos del socio que todavía no se devolvieron."""
        sentencia = (
            select(func.count())
            .select_from(Prestamo)
            .where(col(Prestamo.socio_id) == socio_id, col(Prestamo.fecha_devolucion).is_(None))
        )
        return self.session.exec(sentencia).one()

    def find_by_socio(
        self, socio_id: int, *, activos: bool | None, limit: int, offset: int
    ) -> Sequence[Prestamo]:
        sentencia = select(Prestamo).where(col(Prestamo.socio_id) == socio_id)
        if activos is not None:
            col_devolucion = col(Prestamo.fecha_devolucion)
            sentencia = sentencia.where(
                col_devolucion.is_(None) if activos else col_devolucion.is_not(None)
            )
        sentencia = sentencia.order_by(col(Prestamo.id)).offset(offset).limit(limit)
        return self.session.exec(sentencia).all()

    def mark_returned(self, prestamo_id: int, returned_on: date, fine: int) -> bool:
        """Registra la devolución solo si el préstamo seguía abierto; si no, devuelve False."""
        sentencia = (
            update(Prestamo)
            .where(col(Prestamo.id) == prestamo_id, col(Prestamo.fecha_devolucion).is_(None))
            .values(fecha_devolucion=returned_on, multa=fine)
        )
        return self.session.connection().execute(sentencia).rowcount == 1
