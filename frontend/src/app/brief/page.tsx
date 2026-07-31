"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  CalendarDays,
  CheckSquare,
  LayoutDashboard,
  Mail,
  PenSquare,
  RefreshCw,
} from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LinkButton } from "@/components/ui/LinkButton";
import { PageHeader } from "@/components/ui/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { api, type BriefItem, type DailyBrief } from "@/lib/api/client";

// Map markdown elements to Tailwind classes so the model's formatting renders cleanly
// without depending on the typography plugin.
const markdownComponents = {
  p: (props: React.HTMLAttributes<HTMLParagraphElement>) => (
    <p className="mb-3 text-zinc-700 last:mb-0" {...props} />
  ),
  ul: (props: React.HTMLAttributes<HTMLUListElement>) => (
    <ul className="mb-3 list-disc space-y-1 pl-5 text-zinc-700 last:mb-0" {...props} />
  ),
  ol: (props: React.HTMLAttributes<HTMLOListElement>) => (
    <ol className="mb-3 list-decimal space-y-1 pl-5 text-zinc-700 last:mb-0" {...props} />
  ),
  strong: (props: React.HTMLAttributes<HTMLElement>) => (
    <strong className="font-semibold text-zinc-900" {...props} />
  ),
  a: (props: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a className="text-indigo-600 underline" {...props} />
  ),
};

function ItemCard({ item }: { item: BriefItem }) {
  const isEmail = item.kind === "email";
  return (
    <Card className="flex items-start gap-3 p-4">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-zinc-100 text-zinc-500">
        {isEmail ? <Mail className="h-4 w-4" /> : <CalendarDays className="h-4 w-4" />}
      </div>
      <div className="min-w-0 flex-1">
        <div className="break-words font-medium text-zinc-900">{item.title}</div>
        {item.detail && (
          <div className="mt-0.5 break-words text-sm text-zinc-500">{item.detail}</div>
        )}
        {isEmail && (
          <LinkButton
            href={{
              pathname: "/compose",
              query: { sender: item.sender ?? "", subject: item.subject ?? "" },
            }}
            variant="secondary"
            className="mt-3 !min-h-0 px-3 py-1.5 text-xs"
          >
            <PenSquare className="h-3.5 w-3.5" />
            Compose reply
          </LinkButton>
        )}
      </div>
    </Card>
  );
}

export default function BriefPage() {
  const [brief, setBrief] = useState<DailyBrief | null>(null);
  const [pendingApprovals, setPendingApprovals] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    const { data, error } = await api.GET("/api/v1/brief");
    if (error) {
      setError("Could not load the brief. Try refreshing.");
    } else {
      setBrief(data ?? null);
    }
    setLoading(false);

    // Best-effort — a live count on the Approvals shortcut. Approvals is a plain DB
    // query (cheap); unlike Follow-ups, which would mean an extra live Gmail scan on
    // every brief load, so that shortcut deliberately has no live count.
    const { data: approvals } = await api.GET("/api/v1/approvals");
    if (approvals) {
      setPendingApprovals(approvals.filter((a) => a.status === "pending").length);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <AppShell>
      <PageHeader
        title="Daily brief"
        description="What needs your attention today."
        actions={
          <Button variant="secondary" onClick={load}>
            Refresh
          </Button>
        }
      />

      <div className="mb-6 flex flex-wrap gap-2">
        <LinkButton href="/compose">
          <PenSquare className="h-4 w-4" />
          Compose reply
        </LinkButton>
        <LinkButton href="/followups" variant="secondary">
          <RefreshCw className="h-4 w-4" />
          View follow-ups
        </LinkButton>
        <LinkButton href="/approvals" variant="secondary">
          <CheckSquare className="h-4 w-4" />
          See approvals
          {!!pendingApprovals && (
            <span className="ml-0.5 rounded-full bg-amber-100 px-1.5 py-0.5 text-xs font-semibold text-amber-800">
              {pendingApprovals}
            </span>
          )}
        </LinkButton>
      </div>

      {loading && (
        <div className="space-y-6">
          <Card className="space-y-3 p-5">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </Card>
          <div className="space-y-3">
            <Skeleton className="h-20 w-full rounded-xl" />
            <Skeleton className="h-20 w-full rounded-xl" />
            <Skeleton className="h-20 w-full rounded-xl" />
          </div>
        </div>
      )}
      {error && <Alert tone="warning">{error}</Alert>}

      {brief && !loading && (
        <div className="space-y-6">
          {brief.summary && (
            <Card className="p-5">
              <ReactMarkdown components={markdownComponents}>
                {brief.summary}
              </ReactMarkdown>
            </Card>
          )}

          {(brief.items ?? []).length === 0 ? (
            <EmptyState icon={LayoutDashboard} title="No items." />
          ) : (
            <ul className="space-y-3">
              {(brief.items ?? []).map((item, i) => (
                <li key={item.message_id ?? i}>
                  <ItemCard item={item} />
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {!brief && !loading && !error && (
        <EmptyState icon={LayoutDashboard} title="Nothing to brief yet." />
      )}
    </AppShell>
  );
}
