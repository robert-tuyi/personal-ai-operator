# Roadmap

> Reconciled 2026-07-24 against actual delivery order — the phase groupings below no
> longer match the original plan (e.g. the approval queue shipped as day-one
> infrastructure, not a Phase 3 add-on). See CLAUDE.md's "Scope discipline" section and
> `docs/decisions/` for the sequencing decisions behind this.

## Phase 1 — Done

- Repo setup, product docs, wireframes
- Authentication (Google OAuth)
- Gmail and Calendar integration (read)
- Daily brief
- Draft replies in the user's style
- Approval queue + audit log — built alongside drafts, not deferred: invariant #1 (no
  outbound action without approval) made this load-bearing from the start, not a later
  add-on.

## Phase 2 — Done (v1)

- Memory layer (`docs/decisions/0004-memory-layer-deferred.md`): write on send, retrieve
  to inform draft style. Scoped narrowly on purpose — calendar patterns and explicit
  user-stated facts are still out of scope.

## Phase 3 — In progress

- Follow-up engine (v1 shipped): detect sent threads still awaiting a reply, auto-draft a
  nudge, queue it through the existing approval flow.
- Meeting intelligence (transcription → action items) — not started. Needs its own
  decision on an input surface (meeting audio/transcript source) before design can begin.
- ~~Workflow automation~~ — not a scoped feature; doesn't appear in `docs/mvp-scope.md`.
  Dropped from this roadmap as aspirational framing rather than a concrete item.

## Phase 4

- Design partner pilots
- Feedback loop
- Paid beta
