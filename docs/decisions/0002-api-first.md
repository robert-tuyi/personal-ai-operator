# 0002 — API-first architecture with a generated frontend client

- **Status:** Accepted
- **Date:** 2026-06-14

## Context

The product vision (README) anticipates more than one surface over time. The immediate UI
is a Next.js + Tailwind frontend, but we don't want business logic welded to it, and we
don't want a TS frontend and Python backend silently disagreeing about the API shape.

## Decision

Build **API-first** around a shared service layer:

- **Service layer** (`backend/app/services/`) holds all business logic as plain Python
  functions with no HTTP awareness. This is the source of truth.
- **`backend/app/api/v1/`** exposes thin JSON endpoints returning Pydantic models — the
  durable contract.
- The **frontend** consumes a **TypeScript client generated from the backend's OpenAPI
  schema**. Frontend API types are never hand-written.

Rules:
- Route handlers stay thin and call services; no logic in routes.
- Adapters never call each other over HTTP — they share the service layer.

## Consequences

- Bolting on a new UI later (mobile, a different web app) = consuming the existing
  `api/v1/` contract. No core refactor.
- The backend's Pydantic models are the single source of truth across the language
  boundary; regenerating the client is a required step when the API changes (see
  CLAUDE.md → "How to add a feature").
- Slightly more ceremony now (generation step, versioned API) in exchange for not having
  to untangle logic from a UI later.
