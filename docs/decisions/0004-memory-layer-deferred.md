# 0004 — Memory layer deferred to Phase 2

- **Status:** Accepted
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
