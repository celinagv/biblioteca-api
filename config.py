from functools import lru_cache

from pydantic import NonNegativeInt, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parámetros de la aplicación; cada uno se puede redefinir con una variable BIBLIOTECA_*."""

    model_config = SettingsConfigDict(env_prefix="BIBLIOTECA_", env_file=".env")

    database_url: str = "sqlite:///biblioteca.db"
    plazo_prestamo_dias: PositiveInt = 14
    multa_por_dia: NonNegativeInt = 100
    max_prestamos_activos: PositiveInt = 3


@lru_cache
def get_settings() -> Settings:
    """Devuelve siempre la misma instancia: la configuración se lee una sola vez."""
    return Settings()
