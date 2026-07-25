# Deploying to production

Database on **Supabase**, backend on **Railway**, frontend on **Vercel**. This is the
first real (non-localhost) deployment — see
[`docs/decisions/0003-single-tenant-first.md`](decisions/0003-single-tenant-first.md) for
the security work (token encryption, CSRF, cookie hardening, OAuth scope verification,
data-isolation audit) that this deployment is the reason for.

## Architecture

The browser only ever talks to the Vercel domain. `frontend/next.config.ts` rewrites
`/api/*` to the Railway backend (`BACKEND_ORIGIN`), so from the browser's point of view
everything is same-origin — the same reason this works locally (see `RUNNING.md`), just
with real URLs instead of `localhost`. This is why there's no CORS middleware anywhere:
Vercel-to-Railway is a server-side proxy hop, not a cross-origin browser request.

```
Browser --(https, same-origin)--> Vercel (frontend)
                                      |
                                      | rewrites /api/* (server-side)
                                      v
                                   Railway (backend) --> Supabase (Postgres + pgvector)
                                      |
                                      v
                                Google APIs (Gmail, Calendar) / OpenAI
```

Don't switch to the frontend calling Railway directly (cross-origin) unless something
forces it — that trades this simplicity for CORS config and cross-site cookie handling,
which is materially more fragile for a session-cookie-based app.

## Accounts needed

- [Supabase](https://supabase.com)
- [Railway](https://railway.app)
- [Vercel](https://vercel.com)
- Google Cloud Console — already exists; this just adds a redirect URI and test users to
  the existing OAuth client.

## Order of operations

Do these in order — later steps need URLs produced by earlier ones.

### 1. Supabase (database)

1. Create a project. Copy the Postgres connection string (Project Settings → Database).
2. Enable the `pgvector` extension: Database → Extensions → search `vector` → Enable.
   (The Alembic migration also runs `CREATE EXTENSION IF NOT EXISTS vector`, so this is
   belt-and-suspenders, not strictly required first — but confirms the project supports it
   before anything else depends on it.)
3. From a machine with the backend checked out, run migrations against Supabase:
   ```bash
   cd backend
   DATABASE_URL="<supabase connection string, postgresql+psycopg://...>" uv run alembic upgrade head
   ```
   This creates all four tables (`pending_action`, `oauth_token`, `audit_entry`,
   `memory_item`) before anything tries to connect to them.

### 2. Railway (backend)

1. New project → Deploy from GitHub repo → select this repo.
2. Service settings → set **Root Directory** to `backend/`. Railway will pick up
   `backend/railway.json`, which points the build at `Dockerfile.prod` (not the dev
   `Dockerfile` — that one runs `--reload` and hardcodes port 8000, both wrong for prod)
   and sets the healthcheck to `/api/v1/health`.
3. Set environment variables (see the table below). Deploy.
4. Once deployed, Railway assigns a public URL like
   `https://<service>-production.up.railway.app` — note it down, the frontend needs it.
5. Confirm it's up: `curl https://<railway-url>/api/v1/health` → `{"status":"ok"}`.

### 3. Vercel (frontend)

1. New project → import the same GitHub repo.
2. Root Directory → `frontend/`. Framework preset (Next.js) is auto-detected.
3. Set `BACKEND_ORIGIN` to the Railway URL from step 2. Deploy.
4. Vercel assigns a URL like `https://<project>.vercel.app` — note it down.

### 4. Close the loop

1. Back in Railway: set `GOOGLE_REDIRECT_URI` to
   `https://<vercel-domain>/api/v1/auth/callback`, redeploy.
2. Google Cloud Console → APIs & Services → Credentials → the existing OAuth client → add
   `https://<vercel-domain>/api/v1/auth/callback` as an Authorized redirect URI (the
   `localhost:3000` one can stay too — used for local dev, not exclusive).
3. Google Cloud Console → Google Auth Platform → Audience → **Test users** → add the
   Google account(s) of everyone who should be able to log in. The app is in **Testing**
   mode (see "Google OAuth access model" below) — anyone not on this list gets blocked at
   consent, regardless of how correct everything else is.

### 5. Smoke test

Against the real URLs, logged in as a real test user:

- [ ] `GET /api/v1/health` → `200`
- [ ] Log in with Google completes and lands on `/brief`
- [ ] Daily brief loads real data
- [ ] Calendar shows today's events
- [ ] Compose generates a draft, edit it, queue it
- [ ] Approval queue shows the queued action; Approve → Execute actually sends (only once
      you're confident — this really sends an email)
- [ ] Follow-ups loads
- [ ] Log out clears the session

## Environment variables

### Railway (backend)

| Var | Value | Notes |
|---|---|---|
| `DATABASE_URL` | Supabase connection string | changes from local Postgres |
| `APP_ENV` | `production` | flips cookie `https_only` + CSRF-cookie `secure`, **and** the fail-fast check in `config.py` that refuses to boot on default/blank secrets (ADR 0003) |
| `SESSION_SECRET` | freshly generated | `python -c "import secrets; print(secrets.token_urlsafe(48))"` — must NOT be the dev default, `APP_ENV=production` will refuse to start otherwise |
| `TOKEN_ENCRYPTION_KEY` | freshly generated | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` — same refusal applies |
| `GOOGLE_REDIRECT_URI` | `https://<vercel-domain>/api/v1/auth/callback` | changes from localhost |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | same real values as local `.env` | |
| `LLM_PROVIDER` | `openai` (or `anthropic`) | same as local |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | same as local | whichever `LLM_PROVIDER` needs; `OPENAI_API_KEY` is also required regardless for embeddings (memory layer), see ADR 0004 |
| `APP_URL` | `https://<vercel-domain>` | not currently read anywhere in the code (the post-login redirect is relative) — set for documentation hygiene only |
| `PORT` | — | set automatically by Railway; don't set it yourself. `Dockerfile.prod`'s CMD reads it. |

### Vercel (frontend)

| Var | Value | Notes |
|---|---|---|
| `BACKEND_ORIGIN` | the Railway URL from step 2 | read by `next.config.ts`; no other frontend env vars exist today |

## Google OAuth access model

Decided: **Testing mode + manual allowlist**, not Google's verification/publishing
process. Consequences:

- Capped at 100 users total, each added manually as a Test User (step 4.3 above).
- Refresh tokens expire after ~7 days in Testing mode — everyone re-logs in about weekly.
- Two requested scopes (`gmail.send`, `calendar.events`) are Google-classified as
  sensitive/restricted. Testing mode with pre-approved testers avoids the verification
  requirement that would otherwise apply to a publicly-usable ("In Production" status)
  app requesting those scopes. If this project later needs more than 100 users or wants to
  drop the weekly re-login friction, revisit this — expect Google review turnaround time
  and possibly a security assessment (CASA) for the restricted scopes, and check Google's
  current requirements before committing to that path since the exact thresholds and
  process evolve.

## Known risks to watch

- **Vercel rewrite timeouts on slow LLM calls.** Draft generation (quality model) or brief
  generation could take longer than Vercel's proxy is comfortable with under load. If
  users see failures that Railway's logs show as successful (slow but completed) requests,
  this is likely why — the fix is either a faster/streaming response, or (as a last
  resort) calling Railway directly for that one endpoint, which reopens the CORS
  question above.
- **Old plaintext OAuth tokens don't apply here** (fresh Supabase DB, nothing to migrate),
  but worth remembering for future re-deploys: token encryption (ADR 0003) means any row
  written before that change won't decrypt — re-login replaces it.
- Rate limiting / abuse controls don't exist yet (noted in the ADR 0003 audit as
  lower-priority). Fine for a small allowlisted group; revisit if the user list grows.
