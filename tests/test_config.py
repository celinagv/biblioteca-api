import os
from datetime import date

import pytest

from config import Settings, get_settings
from dependencies import get_today


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    # Evita que un .env local o variables BIBLIOTECA_* alteren los valores por defecto
    monkeypatch.chdir(tmp_path)
    for name in [n for n in os.environ if n.startswith("BIBLIOTECA_")]:
        monkeypatch.delenv(name)


def test_default_business_rules() -> None:
    settings = Settings()

    assert settings.plazo_prestamo_dias == 14
    assert settings.multa_por_dia == 100
    assert settings.max_prestamos_activos == 3


def test_environment_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BIBLIOTECA_PLAZO_PRESTAMO_DIAS", "7")

    assert Settings().plazo_prestamo_dias == 7


def test_settings_are_cached() -> None:
    assert get_settings() is get_settings()


def test_get_today_returns_current_date() -> None:
    assert get_today() == date.today()
