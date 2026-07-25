import Link from "next/link";
import { CalendarDays, CheckSquare, LayoutDashboard, PenSquare, RefreshCw, ShieldCheck } from "lucide-react";

const FEATURES = [
  { href: "/brief", label: "Daily brief", detail: "A quick read on what needs attention today.", icon: LayoutDashboard },
  { href: "/calendar", label: "Calendar", detail: "Today's schedule and what's coming up.", icon: CalendarDays },
  { href: "/compose", label: "Compose", detail: "Draft a reply in your own voice.", icon: PenSquare },
  { href: "/followups", label: "Follow-ups", detail: "Threads still waiting on a reply.", icon: RefreshCw },
  { href: "/approvals", label: "Approval queue", detail: "You approve every send.", icon: CheckSquare },
];

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-10 px-6 py-16 text-center">
      <div className="space-y-4">
        <div className="mx-auto flex w-fit items-center gap-1.5 rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs font-medium text-zinc-500 shadow-sm">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
          Nothing sends without your approval
        </div>
        <h1 className="text-4xl font-semibold tracking-tight text-zinc-900 sm:text-5xl">
          Personal AI Operator
        </h1>
        <p className="mx-auto max-w-xl text-balance text-base text-zinc-500 sm:text-lg">
          A daily brief and style-matched draft replies for your inbox — every
          outbound action waits for your explicit approval.
        </p>
      </div>

      <Link
        href="/login"
        className="rounded-lg bg-zinc-900 px-6 py-3 text-sm font-medium text-white shadow-sm transition-colors hover:bg-zinc-700"
      >
        Get started
      </Link>

      <div className="grid w-full gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f) => {
          const Icon = f.icon;
          return (
            <Link
              key={f.href}
              href={f.href}
              className="group flex flex-col items-start gap-3 rounded-xl border border-zinc-200 bg-white p-5 text-left shadow-sm transition-all hover:border-zinc-300 hover:shadow-md"
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-zinc-100 text-zinc-600 transition-colors group-hover:bg-zinc-900 group-hover:text-white">
                <Icon className="h-5 w-5" />
              </div>
              <div>
                <div className="font-medium text-zinc-900">{f.label}</div>
                <div className="mt-0.5 text-sm text-zinc-500">{f.detail}</div>
              </div>
            </Link>
          );
        })}
      </div>
    </main>
  );
}
