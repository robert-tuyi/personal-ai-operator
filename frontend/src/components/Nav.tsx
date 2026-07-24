"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api/client";

const links = [
  { href: "/brief", label: "Daily brief" },
  { href: "/compose", label: "Compose" },
  { href: "/followups", label: "Follow-ups" },
  { href: "/approvals", label: "Approval queue" },
];

export function Nav() {
  const router = useRouter();

  async function logout() {
    await api.POST("/api/v1/auth/logout");
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="border-b border-slate-200 bg-white">
      <nav className="mx-auto flex max-w-4xl items-center gap-6 px-6 py-4">
        <Link href="/" className="font-semibold text-slate-900">
          Personal AI Operator
        </Link>
        <div className="flex gap-4 text-sm">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-slate-600 hover:text-slate-900"
            >
              {l.label}
            </Link>
          ))}
        </div>
        <button
          type="button"
          onClick={logout}
          className="ml-auto text-sm text-slate-500 hover:text-slate-900"
        >
          Log out
        </button>
      </nav>
    </header>
  );
}
