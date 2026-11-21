from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session

from models import Autor
from scripts import seed as seed_module
from scripts.seed import seed

TODAY = date(2026, 3, 1)


def _count(client: TestClient, path: str) -> int:
    return len(client.get(path, params={"limit": 100}).json())


def test_seed_loads_a_coherent_dataset(client: TestClient, session: Session) -> None:
    assert seed(session, TODAY) is True

    assert _count(client, "/autores") == 4
    assert _count(client, "/libros") == 5
    assert _count(client, "/socios") == 4
    assert [p["id"] for p in client.get("/socios/1/prestamos?activos=true").json()] == [1]
    assert client.get("/libros?disponibles=false").json()[0]["titulo"].startswith("Seis problemas")
    assert client.get("/libros/4").json()["autores"][1]["nombre"] == "Adolfo Bioy Casares"
    assert client.get("/socios/4").json()["activo"] is False


def test_seed_includes_a_late_return_with_fine(client: TestClient, session: Session) -> None:
    seed(session, TODAY)

    fines = [client.get(f"/prestamos/{i}").json()["multa"] for i in range(1, 5)]

    assert sorted(fines) == [0, 0, 0, 600]


def test_seed_does_nothing_when_the_database_already_has_data(
    client: TestClient, session: Session
) -> None:
    seed(session, TODAY)

    assert seed(session, TODAY) is False
    assert _count(client, "/autores") == 4


def test_main_reports_what_it_did(
    monkeypatch: pytest.MonkeyPatch, engine: Engine, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(seed_module, "engine", engine)
    monkeypatch.setattr(seed_module, "create_db_and_tables", lambda: None)

    seed_module.main()
    seed_module.main()

    lines = capsys.readouterr().out.splitlines()
    assert lines == ["Datos de ejemplo cargados.", "La base ya tiene datos; no se agregó nada."]


def test_pk_rejects_an_unsaved_entity() -> None:
    with pytest.raises(ValueError, match="no fue guardada"):
        seed_module._pk(Autor(nombre="X", nacionalidad="Y"))
