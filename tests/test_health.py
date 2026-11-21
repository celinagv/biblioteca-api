import pytest
from fastapi.testclient import TestClient

from main import create_app


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_creates_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    monkeypatch.setattr("main.create_db_and_tables", lambda: calls.append(1))

    with TestClient(create_app()):  # `with` dispara el lifespan
        pass

    assert calls == [1]
