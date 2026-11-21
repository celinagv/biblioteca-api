from typing import Any

from exceptions import ConflictError
from models.socio import Socio
from repositories.prestamos import PrestamoRepository
from repositories.socios import SocioRepository
from services.base import CrudService


class SocioService(CrudService[Socio]):
    """CRUD de socios más la baja lógica y las reglas de unicidad y borrado."""

    entity_name = "Socio"

    def __init__(self, socios: SocioRepository, prestamos: PrestamoRepository) -> None:
        super().__init__(socios)
        self._socios = socios
        self._prestamos = prestamos

    def deactivate(self, socio_id: int) -> Socio:
        """Baja lógica: el historial se conserva. Repetirla no tiene efecto (idempotente)."""
        socio = self.get(socio_id)
        if not socio.activo:
            return socio
        return self._update(socio, {"activo": False})

    def _check_unique(self, values: dict[str, Any], current_id: int | None) -> None:
        email_recibido = values.get("email")
        if email_recibido is None:
            return
        duplicado = self._socios.get_by_email(email_recibido)
        if duplicado is not None and duplicado.id != current_id:
            raise ConflictError(f"Ya existe un socio con el email {email_recibido}")

    def _check_deletable(self, entity_id: int) -> None:
        if self._prestamos.exists_for_socio(entity_id):
            raise ConflictError(
                "No se puede eliminar al socio porque tiene préstamos registrados; dalo de baja"
            )
