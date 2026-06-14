# 0003 — Single-tenant first

- **Status:** Accepted
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
