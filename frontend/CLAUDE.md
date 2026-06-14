# Frontend — conventions

Next.js (App Router) + Tailwind + TypeScript. Read the root `CLAUDE.md` first; this covers
frontend specifics. End-to-end run steps live in `../RUNNING.md`.

## Layout

```
src/
  app/                 Next.js App Router routes (one folder per page) + globals.css
    page.tsx           landing
    login/             "Log in with Google"
    brief/             daily brief (GET /brief)
    compose/           draft a reply (POST /drafts) + queue it (POST /drafts/send)
    approvals/         approval queue (GET /approvals) + approve/reject/execute
  components/          shared UI (Nav)
  lib/api/
    schema.d.ts        GENERATED OpenAPI types — DO NOT EDIT BY HAND
    client.ts          typed openapi-fetch client + model aliases
next.config.ts         /api/* rewrite → backend (same-origin cookies)
```

## The generated-client rule (ADR 0002 — non-negotiable)

The frontend's API types are **generated from the backend's OpenAPI schema**. Never
hand-write request/response shapes; never edit `src/lib/api/schema.d.ts`. The backend's
Pydantic models are the single source of truth across the language boundary.

Regenerate whenever the backend API changes:

```bash
# Backend must be running on http://localhost:8000 (see ../backend/README.md):
npm run gen:api          # reads http://localhost:8000/openapi.json -> src/lib/api/schema.d.ts
```

Offline / CI alternative — dump the schema to a file first, then generate from it:

```bash
cd ../backend && uv run python -c \
  "import json; from app.main import app; open('../frontend/openapi.json','w').write(json.dumps(app.openapi()))"
cd ../frontend && npm run gen:api:file   # reads ./openapi.json
```

Consume the generated types only through `src/lib/api/client.ts` (the `api` object and the
exported model aliases like `DailyBrief`, `PendingAction`).

## Same-origin proxy & auth

Auth is a signed **session cookie** set by the backend. To keep cookies simple locally,
`next.config.ts` proxies `/api/*` to the backend, so the browser only ever talks to the
frontend origin. The API client therefore uses `baseUrl: ""` (relative) with
`credentials: "include"`. Because of the proxy, the Google OAuth redirect URI should be the
**frontend** callback (`http://localhost:3000/api/v1/auth/callback`) so the post-login
`Set-Cookie` lands on the frontend origin. See `../RUNNING.md`.

Override the backend target with the `BACKEND_ORIGIN` env var if it isn't on :8000.

## Conventions

- Pages are thin: fetch via `api`, render with Tailwind. No business logic in the UI.
- **Never weaken the approval flow.** The UI proposes (`POST /drafts/send` creates a PENDING
  action) and approves; the backend gates execution. Execute is disabled until approved, and
  the backend independently refuses to execute anything unapproved (409). Do not add a path
  that sends directly.
- No heavy state libraries — local component state + the typed client is enough.
- No secrets in the frontend. Anything sensitive lives behind the backend.

## Commands

```bash
npm install      # install deps
npm run dev      # dev server on :3000 (proxies /api to :8000)
npm run build    # production build — also type-checks and lints
npm run lint     # ESLint
npm run gen:api  # regenerate the API client (backend must be running)
```
