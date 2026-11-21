"""Errores del dominio. No dependen de HTTP: api/error_handlers.py los traduce a respuestas."""


class DomainError(Exception):
    """Base de los errores de negocio; guarda el mensaje que verá el cliente."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """El recurso pedido no existe."""


class EntityNotFoundError(NotFoundError):
    """No hay ninguna entidad con el id indicado."""

    def __init__(self, entity: str, entity_id: int | str) -> None:
        super().__init__(f"{entity} con id {entity_id} no encontrado")


class ConflictError(DomainError):
    """La operación choca con el estado actual (duplicados, falta de stock, topes)."""


class ForbiddenError(DomainError):
    """La operación no está permitida para este recurso (por ejemplo, un socio dado de baja)."""
