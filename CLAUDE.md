# Personal AI Operator — Engineering Guide

This file is the contract for anyone — human or AI — working in this repo. Read it
before making changes. It overrides habits and defaults.

## What this is

A personal AI operator that learns a user's work style and helps handle email,
scheduling, follow-ups, and meeting notes — always with a human approving outbound
actions. See `README.md` and `docs/` for the product vision; treat those docs as the
source of truth for *intent*.

## How this codebase is maintained

This codebase is extended primarily through AI assistants. That shapes every rule below.
Optimize for:

- **Clarity over cleverness.** Boring, conventional code that's safe to modify beats
  elegant code that needs an expert to touch.
- **Small, reversible changes.** One concern per change. Easy to review, easy to undo.
- **Guardrails over trust.** If something must never happen, encode it in one place and
  make violating it hard — don't rely on a careful reviewer catching it.

## Working on changes (default behavior)

When asked to make a change, unless told otherwise:

- Work on a **new branch**, not `main`. Keep changes to one concern.
- **Show evidence before claiming done** — tests passing and/or the app building/running.
  Don't report "done" without it; "I couldn't verify X" is a valid, preferred answer.
- **Never ask the user to paste secrets or keys.** Tell them where to set the value in
  `.env`; the value never goes through chat or into a tracked file.
- When the user asks how something works or whether to proceed, **explain in plain English**
  before acting.

## Non-negotiable invariants

1. **No outbound action without explicit human approval.** The system NEVER sends email,
   replies, or creates/edits/deletes calendar events directly. Every outbound action is
   written as a *pending action* that the user explicitly approves. This is enforced in a
   single chokepoint (`backend/app/core/approval.py`) — never bypass it, never scatter the
   logic, never add a "just this once" direct call. This is the product's core promise.
2. **Every outbound action is recorded in the audit log** (`backend/app/core/audit.py`) —
   what was proposed, approved, and executed, with timestamps. No silent actions.
3. **Secrets never enter git.** No keys, tokens, or `.env` files committed. Config comes
   from environment variables via `backend/app/config.py`. See `.env.example` for the shape.
4. **All schema changes go through Alembic migrations.** Never hand-edit the database or
   mutate models without a migration.
5. **The backend Pydantic models are the single source of truth for the API contract.**
   The frontend's API types are *generated* from the backend's OpenAPI schema — never
   hand-written. Don't let the two sides drift.

## Scope discipline

Building the wrong thing fast is still building the wrong thing. The product vision is
broad (see `docs/`), but we build it in **thin slices** and prove each before widening.

**Build now (first slice):**
- Google login (OAuth) — this is both authentication and the Gmail/Calendar grant
- Read recent inbox + today's calendar
- **Daily brief** (cheap model)
- **Draft replies in the user's style** (better model), shown in an approval queue

**Planned, NOT yet — do not build without an explicit decision:**
- Personal memory / vector retrieval layer (Phase 2 — see `docs/decisions/0004-memory-layer-deferred.md`)
- Follow-up engine
- Meeting intelligence (transcription → action items)
- Docs/tasks connectors
- Multi-user / multi-tenant (we are single-tenant first — see `docs/decisions/0003-single-tenant-first.md`)
- Autonomous sending of any kind (violates invariant #1, ever)

If a request pulls toward the "not yet" list, stop and confirm before proceeding.

## Architecture (API-first)

The **service layer is the source of truth.** Business logic lives in plain Python
functions with no HTTP awareness. Two thin adapters sit on top:

- `backend/app/api/v1/` — JSON endpoints returning Pydantic models. The durable contract
  for any current or future UI.
- `frontend/` — Next.js + Tailwind, consuming the generated typed API client.

Routes stay thin; they call services. Never put business logic in a route handler.
Never have one adapter call another over HTTP — both call the shared service layer.

See `docs/decisions/0002-api-first.md` for the rationale.

## Tech stack

- **Backend:** Python · FastAPI · SQLModel + Alembic · Authlib (Google OAuth) · httpx.
  Managed with `uv`. Lint/format with `ruff`. Tests with `pytest`.
- **Frontend:** Next.js (App Router) · Tailwind · TypeScript. API client generated from
  backend OpenAPI.
- **Data:** PostgreSQL (Supabase free tier). `pgvector` reserved for the future memory layer.
- **AI:** Anthropic API. **Default to the cheapest capable model (Haiku);** use a stronger
  model (Sonnet) only where output quality is the point (draft generation). Latest model
  IDs and usage live in the `claude-api` reference — consult it before writing model code.
- **Deploy:** backend on Railway/Fly, frontend on Vercel. Free tier throughout.

Where things live:
```
backend/app/domain/      Pydantic models — the contracts
backend/app/services/    real business logic (no HTTP)
backend/app/api/v1/      JSON API adapters
backend/app/integrations/ external clients (google.py, llm.py) — swappable
backend/app/core/        auth, approval chokepoint, audit log, shared deps
backend/app/db/          SQLModel models + Alembic migrations
frontend/src/app/        Next.js routes + Tailwind UI
frontend/src/lib/api/    GENERATED typed client (never hand-edit)
```

## Cost discipline (we are on free tiers)

- Cheapest capable model by default; escalate only with reason.
- **Never feed a whole inbox into a prompt.** Select and trim what the model needs.
- Cache where it helps. Be mindful that LLM calls cost real money even when hosting is free.

## Testing

Write tests where they earn their keep — not coverage theater.

- **Required:**
  - Every `services/` function with real logic.
  - The approval chokepoint and audit log — test these hard, including the negative path
    (the system must *refuse* to act when there's no approval). These protect invariant #1.
  - Any parsing or transformation of model output or external API responses.
  - Every bug fix gets a regression test that fails before the fix and passes after.
- **Light or skip:** thin route handlers, Jinja/Next templates, generated code, trivial
  pass-through.
- Tests live under `backend/tests/`, mirroring the package layout. Use `pytest`.
- **Mock external calls** (Google, Anthropic) — tests never hit live APIs and never spend
  tokens.

## How to add a feature

1. Model the data: add/extend Pydantic models in `domain/` (and a SQLModel + Alembic
   migration if it touches the DB).
2. Write the logic in a `services/` function. No HTTP, no framework types — just inputs
   and outputs. This is where the real work and the tests go.
3. Cover it with tests (see Testing).
4. Expose it via a thin route in `api/v1/`.
5. Regenerate the frontend API client, then build the UI in `frontend/`.
6. If the feature produces an outbound action, route it through the approval chokepoint —
   never around it.

## Definition of done

A change is done only when:
- It does what was asked and nothing it wasn't asked to do.
- `ruff` is clean and `pytest` passes (backend); the frontend builds.
- New `services/` logic and any invariant-touching path have tests (see Testing).
- Any outbound-action path goes through approval + audit.
- No secrets added; any schema change has a migration.

Verify these before claiming completion. If you can't verify, say so explicitly.

## Pointers

- Decisions and their rationale: `docs/decisions/`
- Product vision: `README.md`, `docs/*.md`
- Backend/frontend specifics: `backend/CLAUDE.md`, `frontend/CLAUDE.md`
