from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

settings = get_settings()
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=False, connect_args=_connect_args)


def init_db() -> None:
    """Create tables for local SQLite as a dev convenience.

    For Postgres, schema is owned by Alembic migrations (CLAUDE.md invariant #4) and this
    is a no-op.
    """
    if settings.database_url.startswith("sqlite"):
        import app.db.models  # noqa: F401  (register tables on metadata)

        SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
