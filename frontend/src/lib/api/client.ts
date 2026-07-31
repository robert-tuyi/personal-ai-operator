/**
 * Typed API client.
 *
 * Types come from `./schema.d.ts`, which is GENERATED from the backend's OpenAPI schema
 * (see ADR 0002 and frontend/CLAUDE.md). NEVER hand-edit `schema.d.ts` and never hand-write
 * request/response shapes here — regenerate with `npm run gen:api` when the backend changes.
 *
 * baseUrl is empty so every request is relative to the current (frontend) origin. Next.js
 * rewrites then proxy `/api/*` to the backend, keeping the session cookie same-origin.
 */
import createClient from "openapi-fetch";
import type { paths } from "./schema";

export const api = createClient<paths>({
  baseUrl: "",
  // Send the session cookie on every request. Same-origin via the Next proxy, so this is safe.
  credentials: "include",
});

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const CSRF_COOKIE_NAME = "csrf_token";
const CSRF_HEADER_NAME = "x-csrf-token";

function readCookie(name: string): string | undefined {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : undefined;
}

// CSRF defense-in-depth (ADR 0003, backend/app/core/csrf.py): echo the non-HttpOnly
// csrf_token cookie back as a header on state-changing requests. A cross-site attacker page
// can make the browser send the session cookie automatically, but can't read this cookie's
// value to put in a header — only same-origin JS (this) can.
api.use({
  onRequest({ request }) {
    if (UNSAFE_METHODS.has(request.method)) {
      const token = readCookie(CSRF_COOKIE_NAME);
      if (token) request.headers.set(CSRF_HEADER_NAME, token);
    }
    return request;
  },
});

/** Convenience: typed model aliases pulled from the generated schema. */
export type AuthStatus =
  paths["/api/v1/auth/me"]["get"]["responses"]["200"]["content"]["application/json"];
export type DailyBrief =
  paths["/api/v1/brief"]["get"]["responses"]["200"]["content"]["application/json"];
export type CalendarView =
  paths["/api/v1/calendar"]["get"]["responses"]["200"]["content"]["application/json"];
export type CalendarEvent = NonNullable<CalendarView["today"]>[number];
export type DraftReply =
  paths["/api/v1/drafts"]["post"]["responses"]["200"]["content"]["application/json"];
export type PendingAction =
  paths["/api/v1/approvals"]["get"]["responses"]["200"]["content"]["application/json"][number];
export type FollowUpSuggestion =
  paths["/api/v1/followups"]["get"]["responses"]["200"]["content"]["application/json"][number];
export type IncomingMessage = NonNullable<
  paths["/api/v1/drafts"]["post"]["requestBody"]
>["content"]["application/json"];
export type UserSettings =
  paths["/api/v1/user-settings"]["get"]["responses"]["200"]["content"]["application/json"];
