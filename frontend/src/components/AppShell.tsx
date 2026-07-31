"use client";

import { useEffect, type ReactNode } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  CalendarDays,
  CheckSquare,
  History,
  LayoutDashboard,
  LogOut,
  PenSquare,
  RefreshCw,
  Settings,
} from "lucide-react";
import { api } from "@/lib/api/client";

const NAV_LINKS = [
  { href: "/brief", label: "Daily brief", icon: LayoutDashboard },
  { href: "/calendar", label: "Calendar", icon: CalendarDays },
  { href: "/compose", label: "Compose", icon: PenSquare },
  { href: "/followups", label: "Follow-ups", icon: RefreshCw },
  { href: "/approvals", label: "Approval queue", icon: CheckSquare },
  { href: "/activity", label: "Activity log", icon: History },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  // Renders on every authenticated page, so this is what guarantees the CSRF cookie
  // (ADR 0003, backend/app/core/csrf.py) exists before the user can trigger a POST —
  // some pages (e.g. compose) don't otherwise make any GET request on their own.
  //
  // Also the single choke point for the onboarding gate: the OAuth callback
  // (backend/app/api/v1/auth.py) redirects straight to /brief server-side, so this is
  // where a first-time user actually gets steered to /onboarding instead — every
  // AppShell page checks the same flag, rather than duplicating the check per page.
  useEffect(() => {
    api.GET("/api/v1/auth/me");
    api.GET("/api/v1/user-settings").then(({ data }) => {
      if (data && !data.onboarding_completed) {
        router.replace("/onboarding");
      }
    });
  }, [router]);

  async function logout() {
    await api.POST("/api/v1/auth/logout");
    router.push("/login");
    router.refresh();
  }

  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-60 flex-col border-r border-zinc-200 bg-white md:flex">
        <Link
          href="/"
          className="flex h-16 items-center gap-2.5 border-b border-zinc-100 px-5"
        >
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-zinc-900 text-xs font-bold text-white">
            AI
          </div>
          <span className="text-sm font-semibold leading-tight text-zinc-900">
            Personal AI Operator
          </span>
        </Link>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_LINKS.map((link) => {
            const active = pathname === link.href;
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "bg-zinc-900 text-white"
                    : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
                }`}
              >
                <Icon className="h-4 w-4" strokeWidth={2} />
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-zinc-100 p-3">
          <button
            type="button"
            onClick={logout}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-900"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
      </aside>

      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-zinc-200 bg-white/90 px-4 py-3 backdrop-blur md:hidden">
        <Link href="/" className="text-sm font-semibold text-zinc-900">
          Personal AI Operator
        </Link>
        <button
          type="button"
          onClick={logout}
          className="flex min-h-[44px] items-center gap-1.5 px-2 text-sm font-medium text-zinc-500"
        >
          <LogOut className="h-4 w-4" />
          Log out
        </button>
      </header>
      <nav className="flex gap-1 overflow-x-auto border-b border-zinc-200 bg-white px-3 py-2 md:hidden">
        {NAV_LINKS.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`inline-flex min-h-[40px] shrink-0 items-center whitespace-nowrap rounded-md px-3 py-2 text-xs font-medium transition-colors ${
                active
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-600 hover:bg-zinc-100"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="md:pl-60">
        <main className="mx-auto max-w-5xl px-6 py-8 md:py-10 lg:px-10">
          {children}
        </main>
      </div>
    </div>
  );
}
