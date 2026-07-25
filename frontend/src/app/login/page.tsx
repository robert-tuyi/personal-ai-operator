"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck } from "lucide-react";
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
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-8 px-6 text-center">
      <div className="space-y-3">
        <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-900 text-sm font-bold text-white">
          AI
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          Log in
        </h1>
        <p className="text-sm leading-relaxed text-zinc-500">
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
        className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 bg-white px-5 py-2.5 text-sm font-medium text-zinc-800 shadow-sm transition-colors hover:bg-zinc-50"
      >
        <span className="text-base font-semibold">G</span>
        Log in with Google
      </a>

      <div className="flex items-center gap-1.5 text-xs text-zinc-400">
        <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
        Nothing is ever sent without your explicit approval.
      </div>

      {status && !status.authenticated && (
        <p className="text-xs text-zinc-400">You are not logged in yet.</p>
      )}
    </main>
  );
}
