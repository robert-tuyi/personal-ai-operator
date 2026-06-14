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

/** Convenience: typed model aliases pulled from the generated schema. */
export type AuthStatus =
  paths["/api/v1/auth/me"]["get"]["responses"]["200"]["content"]["application/json"];
export type DailyBrief =
  paths["/api/v1/brief"]["get"]["responses"]["200"]["content"]["application/json"];
export type DraftReply =
  paths["/api/v1/drafts"]["post"]["responses"]["200"]["content"]["application/json"];
export type PendingAction =
  paths["/api/v1/approvals"]["get"]["responses"]["200"]["content"]["application/json"][number];
export type IncomingMessage = NonNullable<
  paths["/api/v1/drafts"]["post"]["requestBody"]
>["content"]["application/json"];
