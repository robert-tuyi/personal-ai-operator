import type { NextConfig } from "next";

/**
 * The browser talks to the frontend origin only. We proxy every /api/* request to the
 * FastAPI backend so that, from the browser's point of view, everything is same-origin.
 *
 * Why this matters: auth is a signed session cookie set by the backend. If the browser
 * called the backend on a different origin (localhost:8000), the Set-Cookie would land on
 * that origin and cross-origin cookie rules (SameSite, credentials) would bite us locally.
 * By proxying, the cookie is set on the frontend origin (localhost:3000) and "just works".
 *
 * Because of this, the Google OAuth redirect URI should point at the FRONTEND callback:
 *     http://localhost:3000/api/v1/auth/callback
 * so the post-login Set-Cookie also lands on the frontend origin. See ../RUNNING.md.
 */
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_ORIGIN}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
