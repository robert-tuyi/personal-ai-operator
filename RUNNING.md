# Running Personal AI Operator locally

End-to-end local setup for the FastAPI backend and the Next.js frontend together.

The headline: **you can run and click through the whole app with NO Google or Anthropic
credentials.** Those credentials only unlock the parts that talk to Google/Anthropic. See
"What you can test at each stage" at the bottom.

## Prerequisites

- Python with [`uv`](https://docs.astral.sh/uv/) (backend)
- Node.js 18+ and npm (frontend) — developed against Node 22 / npm 10

## 1. Backend

```bash
cd backend
uv sync                       # install deps
cp .env.example .env          # then fill in keys (see below)
uv run uvicorn app.main:app --reload   # serves http://localhost:8000
```

`.env` values:

| Var | Needed for | If left blank |
| --- | --- | --- |
| `DATABASE_URL` | — | defaults to local SQLite, auto-created. Leave as-is. |
| `SESSION_SECRET` | signing the login cookie | a dev default is used; fine locally |
| `ANTHROPIC_API_KEY` | real brief + draft text | LLM calls fail; everything else works |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` | logging in with Google | login can't complete, and the authenticated data endpoints (brief, approvals, queue-send) return 401 |

Verify it's up: `curl http://localhost:8000/api/v1/health` → `{"status":"ok"}`.
Interactive API + OpenAPI schema: http://localhost:8000/docs.

## 2. Frontend

```bash
cd frontend
npm install
npm run gen:api               # generate the typed API client (backend must be running)
npm run dev                   # serves http://localhost:3000
```

Open http://localhost:3000.

### Why the frontend proxies /api

`frontend/next.config.ts` rewrites `/api/*` to `http://localhost:8000`, so the browser only
ever talks to the frontend origin (`localhost:3000`). Auth is a **signed session cookie** set
by the backend; keeping everything same-origin means the cookie "just works" locally without
cross-origin cookie headaches. Override the backend target with `BACKEND_ORIGIN` if needed.

### Regenerating the API client (ADR 0002)

API types are **generated**, never hand-written. Re-run after any backend API change:

```bash
npm run gen:api          # from live backend at http://localhost:8000/openapi.json
# or, offline:
cd ../backend && uv run python -c \
  "import json; from app.main import app; open('../frontend/openapi.json','w').write(json.dumps(app.openapi()))"
cd ../frontend && npm run gen:api:file
```

## 3. Google OAuth setup (only when you want real login)

All in the [Google Cloud Console](https://console.cloud.google.com), in order:

1. **Create/select a project** (top-bar project picker → New Project).
2. **Enable APIs** — APIs & Services → Library → enable **Gmail API** and **Google Calendar
   API**. Skipping this makes the calls 403.
3. **Consent screen** (Google Auth Platform, a.k.a. OAuth consent screen):
   - Audience: **External**, kept in **Testing** (do not publish).
   - Add your login account under **Test users** — required, or login is blocked.
   - No need to pre-declare scopes; the app requests them at login.
4. **Create the client** — Credentials → Create credentials → OAuth client ID → **Web
   application**. Add this exact **Authorized redirect URI** (frontend origin, because the
   frontend proxies `/api/*` so the login `Set-Cookie` lands on `:3000`):

   ```
   http://localhost:3000/api/v1/auth/callback
   ```

5. Copy the client ID/secret into `backend/.env`:

   ```
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   GOOGLE_REDIRECT_URI=http://localhost:3000/api/v1/auth/callback
   ```

   (A backend-direct setup using `:8000` is noted in `backend/.env.example`; the
   frontend-proxy URI above is what you want when running the UI.)

Single-user testing mode needs no Google verification (ADR 0003). Two things to expect at
login:

- An **"unverified app"** screen — Advanced → "Go to … (unsafe)". Normal; only test users
  reach it.
- Testing mode **expires the refresh token after ~7 days**, so you'll re-login about weekly
  until the app is published/verified.

## What you can test at each stage

### (a) With NO external setup — just `uv sync` + `npm install`

These work against the live local backend with zero credentials:

- **App loads & navigates.** Landing, Login, Brief, Compose, Approvals pages render and the UI
  is reachable end to end.
- **The generated API client (ADR 0002).** `npm run gen:api` succeeds against the live backend
  and the whole UI is typed from it. This is the headline thing you can prove with no creds.
- **Backend health and the full API surface** via http://localhost:8000/docs.
- **The same-origin proxy.** `curl http://localhost:3000/api/v1/health` returns the backend's
  `{"status":"ok"}` through the Next.js rewrite.
- **`POST /drafts` (generate a draft) is wired** but needs `ANTHROPIC_API_KEY` to return text
  (see (c)); without it the draft endpoint errors.

> Auth gate: on this branch the data endpoints (`GET /brief`, `POST /drafts/send`,
> `GET /approvals` and the approve/reject/execute routes) require a logged-in session and
> return **401** until you log in with Google. So the brief view and the live approval queue
> need the Google setup in (b) to show real data. The approval *gate* itself
> (`execute` refusing an unapproved action with **409**) is exercised by the backend tests
> (`backend/tests/test_approval.py`) and visible in the UI: Execute stays disabled until a row
> is Approved, and the backend independently refuses regardless.

### (b) Requires Google OAuth credentials

- **"Log in with Google"** completing the consent flow and setting the session cookie.
- **Any authenticated endpoint at all:** the daily brief, queuing a draft for sending, and the
  entire approval queue (list / approve / reject / execute) — all return 401 until you log in,
  so a logged-in session is the thing that lights up the approval flow in the UI.
- **Real inbox / calendar data** feeding the daily brief (Gmail/Calendar read).
- **Actually sending** an approved email / creating a calendar event on Execute (the Google
  write integration; still only ever after explicit approval).

### (c) Requires `ANTHROPIC_API_KEY`

- **Real daily-brief text** (cheap model) and **style-matched draft replies** (quality model).
  Without the key these LLM-backed endpoints error; the approval machinery around them does
  not depend on the key.

## Quick verification checklist

```bash
# backend
cd backend && uv run ruff check . && uv run pytest

# frontend (backend must be running for gen:api)
cd frontend && npm install && npm run gen:api && npm run build && npm run lint
```
