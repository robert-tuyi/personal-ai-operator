from collections.abc import Iterator

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import app.db.models  # noqa: F401  (register tables on metadata)


@pytest.fixture
def session() -> Iterator[Session]:
    """A fresh in-memory SQLite DB per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
