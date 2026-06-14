# 0001 — Python backend (not Node)

- **Status:** Accepted
- **Date:** 2026-06-14

## Context

`architecture.md` specified the backend as "Node.js or Python" — a choice left open. We
needed to pick one. The backend's workload is mostly I/O orchestration (Google APIs,
Anthropic API, Postgres), plus heavy validation of structured model output and a likely
future of AI/data-flavored work (memory layer, evals, email-pattern analysis).

## Decision

Use **Python** with **FastAPI**.

Rationale:
- **Structured-output validation** is central to this product. Pydantic is best-in-class
  for validating JSON returned by models, and the Python AI ecosystem is built around it.
- **Future AI/data work** (the planned memory layer, evaluation pipelines) is Python's home
  turf.
- FastAPI auto-generates an OpenAPI schema, which we use to generate the frontend's typed
  client — keeping the cross-language contract honest (see 0002).
- The backend workload is I/O-bound glue, where Python's async is more than adequate.

## Consequences

- The repo spans **two languages** (Python backend, TypeScript frontend). We accept this to
  honor the frontend choice in `architecture.md` (Next.js + Tailwind). The OpenAPI-generated
  client (0002) is the mitigation that keeps the split from drifting.
- Tooling: `uv` for packaging, `ruff` for lint/format, `pytest` for tests.
- If we later need a slick SPA we already have the JSON API; if we ever wanted one language
  we'd revisit, but that's not on the table.
