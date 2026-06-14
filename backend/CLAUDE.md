# Backend — conventions

Python + FastAPI. Read the root `CLAUDE.md` first; this covers backend specifics. Run
instructions are in `README.md`.

## Layout

```
app/
  main.py            FastAPI app factory + ApprovalError → 409 handler
  config.py          pydantic-settings (env only; no hardcoded secrets)
  domain/            Pydantic models — the API contract (actions, brief, drafts)
  services/          business logic, no HTTP — dependencies injected for testability
  api/v1/            thin routers; call services; map nothing else
  integrations/      external clients: google.py (Gmail/Calendar), google_oauth.py
                     (login + token refresh), llm.py (Anthropic)
  core/              approval.py (the chokepoint), audit.py, deps.py
  services/oauth_tokens.py   OAuth token persistence (owner-scoped)
  db/                session.py, models.py (SQLModel), migrations/ (Alembic)
tests/               pytest; in-memory SQLite via conftest.py
```

## Rules specific to the backend

- **Logic goes in `services/`**, written as plain functions with injected dependencies
  (see `services/brief.py` — the summarizer is passed in). Routers in `api/v1/` stay thin.
- **Outbound side effects only through `core/approval.py`.** To cause one, `propose()` an
  action and register an executor in the owning integration (see `google.py`). Never call
  a write API from a service or route. The `execute_approved()` refuse-if-unapproved path
  is covered by `tests/test_approval.py` — keep that test strong.
- **Thread `owner_id` through everything.** Single-tenant today (one fixed owner in
  `core/deps.py`), but rows are owner-scoped so multi-tenant is an extension (ADR 0003).
- **Models are the contract.** Add/extend Pydantic models in `domain/`; the frontend's TS
  client is generated from the OpenAPI schema these produce.
- **Schema changes via Alembic** (`alembic revision --autogenerate`). Local SQLite is
  auto-created for convenience, but migrations own the real schema.
- **LLM:** default `llm.complete(...)` (cheap model); pass `quality=True` only where output
  is the point (drafts). Never send a whole inbox into a prompt.

## Needs live credentials, not code

These paths are fully implemented — the gap is supplying real credentials, not writing code:

- `integrations/google.py` — Gmail/Calendar read + write are wired. Needs a Google OAuth
  client (`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`) and a logged-in owner.
- `integrations/google_oauth.py` + `api/v1/auth.py` + `services/oauth_tokens.py` — the
  "Log in with Google" flow (redirect/callback, token storage, refresh) is built.
  `core/deps.py` resolves the owner from the session cookie.
- `integrations/llm.py` — real Anthropic calls; needs `ANTHROPIC_API_KEY`.

## Definition of done (backend)

`uv run ruff check .` clean, `uv run pytest` green, new `services/` logic and any
approval/audit path tested. See root `CLAUDE.md` for the full checklist.
