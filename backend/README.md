# Backend

FastAPI service. See `CLAUDE.md` for conventions and `../docs/decisions/` for the why.

## Run locally

```bash
uv sync                       # install deps
cp .env.example .env          # then fill in keys
uv run uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API (and the OpenAPI schema the
frontend client is generated from).

## Tests & lint

```bash
uv run pytest
uv run ruff check .
```

## Migrations

Schema changes go through Alembic (never hand-edit the DB):

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

Local SQLite is created automatically on first run for convenience; Postgres schema is
managed by migrations.
