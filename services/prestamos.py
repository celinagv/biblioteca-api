from collections.abc import Sequence
from datetime import date, timedelta

from api.schemas.prestamo import PrestamoCreate
from config import Settings
from exceptions import ConflictError, EntityNotFoundError, ForbiddenError
from models.libro import Libro
from models.prestamo import Prestamo
from models.socio import Socio
from repositories.libros import LibroRepository
from repositories.prestamos import PrestamoRepository
from repositories.socios import SocioRepository


def calculate_fine(due_date: date, returned_on: date, daily_rate: int) -> int:
    """Multa = días de atraso por la tarifa diaria; si se devolvió en término, es 0."""
    return max(0, (returned_on - due_date).days) * daily_rate


class PrestamoService:
    """Reglas de los préstamos: quién puede pedir, control de stock, vencimiento y multas."""

    def __init__(
        self,
        prestamos: PrestamoRepository,
        socios: SocioRepository,
        libros: LibroRepository,
        settings: Settings,
    ) -> None:
        self._prestamos = prestamos
        self._socios = socios
        self._libros = libros
        self._settings = settings

    def get(self, prestamo_id: int) -> Prestamo:
        loan = self._prestamos.get(prestamo_id)
        if loan is None:
            raise EntityNotFoundError("Préstamo", prestamo_id)
        return loan

    def list_by_socio(
        self, socio_id: int, *, activos: bool | None, limit: int, offset: int
    ) -> Sequence[Prestamo]:
        self._get_socio(socio_id)
        return self._prestamos.find_by_socio(socio_id, activos=activos, limit=limit, offset=offset)

    def create(self, data: PrestamoCreate, today: date) -> Prestamo:
        # El orden de los chequeos es parte del contrato: 404 -> 403 -> 409 (tope) -> 409 (stock)
        member = self._get_socio(data.socio_id)
        self._get_libro(data.libro_id)
        self._ensure_can_borrow(member, data.socio_id)
        if not self._libros.take_one_from_stock(data.libro_id):
            raise ConflictError(f"El libro {data.libro_id} no tiene stock disponible")

        loan = Prestamo(
            socio_id=data.socio_id,
            libro_id=data.libro_id,
            fecha_prestamo=today,
            fecha_vencimiento=today + timedelta(days=self._settings.plazo_prestamo_dias),
        )
        self._prestamos.add(loan)
        self._prestamos.commit()  # un único commit confirma a la vez el stock y el préstamo
        self._prestamos.refresh(loan)
        return loan

    def return_loan(self, prestamo_id: int, today: date) -> Prestamo:
        """Cierra el préstamo: calcula la multa, marca la devolución y repone el stock."""
        loan = self.get(prestamo_id)
        if loan.fecha_devolucion is not None:
            raise self._already_returned(prestamo_id)

        book_id = loan.libro_id
        late_fee = calculate_fine(loan.fecha_vencimiento, today, self._settings.multa_por_dia)
        if not self._prestamos.mark_returned(prestamo_id, today, late_fee):
            raise self._already_returned(prestamo_id)  # otra solicitud se adelantó y lo cerró
        self._libros.return_one_to_stock(book_id)
        self._prestamos.commit()
        self._prestamos.refresh(loan)
        return loan

    def _ensure_can_borrow(self, socio: Socio, socio_id: int) -> None:
        """Verifica que el socio esté activo y no haya alcanzado el tope de préstamos."""
        if not socio.activo:
            raise ForbiddenError(f"El socio {socio_id} está inactivo y no puede pedir préstamos")
        max_active = self._settings.max_prestamos_activos
        if self._prestamos.count_active_by_socio(socio_id) >= max_active:
            raise ConflictError(f"El socio {socio_id} ya tiene {max_active} préstamos activos")

    def _get_socio(self, socio_id: int) -> Socio:
        member = self._socios.get(socio_id)
        if member is None:
            raise EntityNotFoundError("Socio", socio_id)
        return member

    def _get_libro(self, libro_id: int) -> Libro:
        book = self._libros.get(libro_id)
        if book is None:
            raise EntityNotFoundError("Libro", libro_id)
        return book

    @staticmethod
    def _already_returned(prestamo_id: int) -> ConflictError:
        return ConflictError(f"El préstamo {prestamo_id} ya fue devuelto")
