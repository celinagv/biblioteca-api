from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from database import get_session
from dependencies import get_today
from main import app


class FakeClock:
    """Reloj controlable: los tests mueven `today` para simular el paso del tiempo."""

    def __init__(self, today: date) -> None:
        self.today = today

    def __call__(self) -> date:
        return self.today


@pytest.fixture
def engine() -> Iterator[Engine]:
    # StaticPool: todas las conexiones comparten la misma base en memoria
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(date(2026, 1, 15))


@pytest.fixture
def client(session: Session, clock: FakeClock) -> Iterator[TestClient]:
    # Sin `with`, TestClient no dispara el lifespan: no se toca la base real
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_today] = clock
    yield TestClient(app)
    app.dependency_overrides.clear()
