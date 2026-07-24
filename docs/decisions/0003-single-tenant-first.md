# 0003 — Single-tenant first

- **Status:** Accepted — security items partially addressed 2026-07-24 (see below)
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
  - CSRF defense-in-depth on state-changing POSTs (approve / reject / execute / logout) —
    still open. `same_site="lax"` (now explicit, above) covers the classic case but isn't
    a substitute for a real token given the blast radius (approving/executing a send).
  - Verify granted OAuth scopes match the requested scopes at the callback — still open.
  - Still fully open: real data isolation audit (though see the note below — the
    foundation is better than this ADR originally assumed), Google OAuth security
    verification, and the multi-tenant decision itself.

## Update — 2026-07-24: isolation foundation reassessed

Re-reading the code while scoping the above: `core/deps.py`'s `current_owner_id` already
derives `owner_id` dynamically from the logged-in Google account's `sub` — it is **not**
a hardcoded single owner, despite CLAUDE.md's description at the time this ADR was written.
Every table (`PendingActionRow`, `OAuthTokenRow`, `AuditEntryRow`, `MemoryItemRow`) is
owner-scoped and every query path checked so far enforces it. Real per-user data isolation
substantially already exists; going multi-user is a verification/hardening pass over what's
here, not a rewrite.
