# 0004 — Memory layer deferred to Phase 2

- **Status:** Superseded — Phase 2 started 2026-07-24 (see below)
- **Date:** 2026-06-14

## Context

A personal memory layer is the owner's #1 stated differentiator (`startup-concept.md`) and
appears in the MVP feature list and `architecture.md` (vector database). It's central to
the long-term product. But the first slice we're building — daily brief + style-matched
draft replies behind an approval gate — can be demonstrated and validated without a
persistent retrieval layer.

## Decision

**Defer** the memory / vector retrieval layer to Phase 2. The first slice ships without it.

- `pgvector` and the Supabase Postgres choice are kept specifically so the memory layer
  drops in later without a data-store migration.
- Style matching in the first slice is done from recent context passed into the prompt, not
  from a persistent learned memory.

## Consequences

- Faster path to a runnable, testable proof of the core experience.
- **Risk acknowledged:** the first slice does not yet showcase the differentiator the owner
  cares most about. This is a deliberate sequencing call, revisited once brief + drafts are
  proven. It is **planned, not dropped** — do not let it fall off the roadmap.
- When built, it slots behind the existing service layer (0002): a retrieval service the
  brief/draft services call. No API contract break expected.

## Update — 2026-07-24: Phase 2 started

Brief + drafts (the first slice) are running end to end, so per this ADR's own consequence
("revisited once brief + drafts are proven"), the memory layer build has started:

- Data store: Postgres + `pgvector`, per the original plan — added to `docker-compose.yml`
  as a `postgres` service (`pgvector/pgvector:pg16`); Supabase for prod, same extension.
- `services/memory.py`: `write_memory()` / `retrieve_relevant()`, exactly the retrieval
  service shape this ADR anticipated. No API contract break — no new routes were added.
- V1 scope is deliberately narrow (thin slice, same discipline as Phase 1): memory is
  written **only** from sent/approved draft replies (the approval executor for
  `SEND_EMAIL`, after the send succeeds — never from a draft or proposal), and read back
  into `services/drafts.py` to inform style. Calendar patterns, explicit user-stated facts,
  and a follow-up engine are still out of scope.
- Embeddings always go through OpenAI (`text-embedding-3-small`), independent of
  `LLM_PROVIDER` — Anthropic has no embeddings API.
