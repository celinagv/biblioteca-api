from typing import Any, Self

from pydantic import BaseModel, ConfigDict, model_validator


class ReadSchema(BaseModel):
    """Base de las respuestas: se construyen a partir de los objetos de la base de datos."""

    model_config = ConfigDict(from_attributes=True)


class PatchSchema(BaseModel):
    """Base de los PATCH: se aplican solo los campos enviados y ninguno puede ser null."""

    @model_validator(mode="after")
    def _reject_explicit_null(self) -> Self:
        null_fields = sorted(name for name in self.model_fields_set if getattr(self, name) is None)
        if null_fields:
            raise ValueError(f"Estos campos no pueden ser null: {', '.join(null_fields)}")
        return self

    def changes(self) -> dict[str, Any]:
        """Devuelve únicamente los campos que el cliente envió de forma explícita."""
        return self.model_dump(exclude_unset=True)
