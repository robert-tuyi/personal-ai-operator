"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, type AuthStatus } from "@/lib/api/client";

export default function LoginPage() {
  const router = useRouter();
  const [status, setStatus] = useState<AuthStatus | null>(null);

  useEffect(() => {
    api.GET("/api/v1/auth/me").then(({ data }) => {
      if (data?.authenticated) {
        router.replace("/brief");
      } else {
        setStatus(data ?? { authenticated: false });
      }
    });
  }, [router]);

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-6 px-6 text-center">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold">Log in</h1>
        <p className="text-sm text-slate-600">
          Logging in with Google also grants read access to your inbox and
          calendar. It never sends anything on its own.
        </p>
      </div>

      {/*
        A plain anchor (full navigation) — the backend route 302-redirects the
        browser to Google's consent screen. Going through fetch would not follow
        the cross-origin redirect to Google.
      */}
      <a
        href="/api/v1/auth/login"
        className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-5 py-2.5 text-sm font-medium text-slate-800 shadow-sm hover:bg-slate-50"
      >
        <span className="text-base">G</span>
        Log in with Google
      </a>

      {status && !status.authenticated && (
        <p className="text-xs text-slate-400">
          You are not logged in yet.
        </p>
      )}
    </main>
  );
}
