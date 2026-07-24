# 0003 — Single-tenant first

- **Status:** Accepted — security items 1-5 addressed 2026-07-24 (see below)
- **Date:** 2026-06-14

## Context

The product vision describes a multi-user SaaS for founders, executives, consultants, and
PMs. The current goal is narrower: validate whether the core idea (a brief + style-matched
draft replies, behind an approval gate) is actually useful, with a single user dogfooding
their own email and calendar.

## Decision

Build **single-tenant** first: one user, their own Google account, their own data.

- No multi-tenancy, no per-user data isolation machinery, no org/admin concepts yet.
- Google OAuth in "testing" mode (<100 users) — no Google security verification needed at
  this stage, which removes a multi-week, possibly-paid blocker.
- Auth is simply "log in with Google," which also yields the Gmail/Calendar grant.

## Consequences

- Dramatically less to build and reason about for the validation phase.
- We must **not foreclose** multi-tenant: keep user-scoping explicit in the data model
  (rows carry an owner) even while there's only one user, so adding tenants later is an
  extension, not a rewrite.
- Going multi-user later will require: Google OAuth verification, real data isolation,
  and a privacy/security review. These are explicitly deferred, not ignored.
- Security items to address before multi-user / prod (deferred, not ignored):
  - ~~Encrypt OAuth tokens at rest~~ — **Done.** `core/crypto.py` (Fernet); DB only ever
    holds ciphertext, `services/oauth_tokens.py` decrypts for callers. Old plaintext rows
    from before this change won't decrypt — re-login to replace them.
  - ~~Fail-fast on the insecure `session_secret` default~~ — **Done**, and extended to
    `token_encryption_key` too: `config.py`'s `Settings` refuses to construct outside
    `development` if either is unset or still the dev-only default.
  - ~~Set cookie `Secure` and a shorter `max_age` in prod~~ — **Done.** `main.py`:
    `https_only` follows `app_env`, `same_site="lax"` explicit, `max_age` down to 7 days
    from Starlette's 14-day default.
  - ~~CSRF defense-in-depth on state-changing POSTs~~ — **Done.** `core/csrf.py`:
    double-submit cookie pattern, applied globally to all POST/PUT/PATCH/DELETE via
    middleware (not per-route) — a non-HttpOnly `csrf_token` cookie must be echoed back as
    an `X-CSRF-Token` header, checked with a constant-time compare. Frontend wiring in
    `lib/api/client.ts` (attaches the header) and `components/Nav.tsx` (fires an early GET
    on every page so the cookie exists before any POST — some pages, e.g. compose, don't
    otherwise make one). The middleware also seeds the cookie on a *refused* request, so a
    client whose very first request is a POST can still recover on retry.
  - ~~Verify granted OAuth scopes match the requested scopes at the callback~~ — **Done.**
    `api/v1/auth.py`'s `callback()` compares granted vs. requested scope and rejects a
    partial grant with 400 (redirect never happens, no session/token is stored). Per
    RFC 6749 §5.1, an absent `scope` field on the token response means "matches what was
    requested" — treated as fully granted, not silently rejected.
  - ~~Real data isolation audit~~ — **Done** (2026-07-24), no gaps found; see the
    2026-07-24 update below for what was checked.
  - Still fully open: Google OAuth security verification, and the multi-tenant decision
    itself.

## Update — 2026-07-24: isolation foundation reassessed

Re-reading the code while scoping the above: `core/deps.py`'s `current_owner_id` already
derives `owner_id` dynamically from the logged-in Google account's `sub` — it is **not**
a hardcoded single owner, despite CLAUDE.md's description at the time this ADR was written.
Every table (`PendingActionRow`, `OAuthTokenRow`, `AuditEntryRow`, `MemoryItemRow`) is
owner-scoped and every query path checked so far enforces it. Real per-user data isolation
substantially already exists; going multi-user is a verification/hardening pass over what's
here, not a rewrite.

### Isolation audit results (2026-07-24)

Walked every DB-touching function and every API route:

- **Every table has an `owner_id` column** — confirmed all four (no others exist).
- **Every query filters by it.** `audit.list_entries`, `approval.list_pending`,
  `memory._similarity_search` all `.where(...owner_id == owner_id)`. `oauth_tokens`'
  `save_token`/`get_token` use `session.get(OAuthTokenRow, owner_id)` — `owner_id` *is* the
  primary key, so it's inherently scoped, not merely filtered.
- **The one lookup-by-client-supplied-ID path is safe.** `approval._get()` fetches a
  `PendingActionRow` by `action_id` (attacker-guessable/enumerable) but then explicitly
  checks `row.owner_id != owner_id` before returning — covered by
  `test_cannot_approve_someone_elses_action`. No other route resolves a row by an ID that
  didn't originate from an owner-scoped query.
- **Every route derives `owner_id` only from `OwnerDep`** (the session cookie, via
  `current_owner_id`) — never from a path param, query param, or request body. Grepped the
  frontend too: `owner_id` never appears in any request the client sends, only as a
  read-only field on the `AuthStatus` response.

No gaps found; no code changes were needed.
