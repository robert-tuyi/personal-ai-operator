"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { LayoutDashboard } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, type DailyBrief } from "@/lib/api/client";

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
  h1: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h2 className="mb-2 mt-4 text-lg font-semibold text-zinc-900 first:mt-0" {...props} />
  ),
  h2: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h3 className="mb-2 mt-4 font-semibold text-zinc-900 first:mt-0" {...props} />
  ),
  strong: (props: React.HTMLAttributes<HTMLElement>) => (
    <strong className="font-semibold text-zinc-900" {...props} />
  ),
  a: (props: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a className="text-indigo-600 underline" {...props} />
  ),
};

export default function BriefPage() {
  const [brief, setBrief] = useState<DailyBrief | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    const { data, error } = await api.GET("/api/v1/brief");
    if (error) {
      setError("Could not load the brief. Are you logged in?");
    } else {
      setBrief(data ?? null);
    }
    setLoading(false);
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

      {loading && <p className="text-sm text-zinc-500">Loading…</p>}
      {error && <Alert tone="warning">{error}</Alert>}

      {brief && !loading && (
        <div className="space-y-6">
          <Card className="p-5">
            {brief.summary ? (
              <ReactMarkdown components={markdownComponents}>
                {brief.summary}
              </ReactMarkdown>
            ) : (
              <p className="text-sm text-zinc-500">Nothing notable today.</p>
            )}
          </Card>

          {(brief.items ?? []).length === 0 ? (
            <EmptyState icon={LayoutDashboard} title="No items." />
          ) : (
            <ul className="space-y-3">
              {(brief.items ?? []).map((item, i) => (
                <li key={i}>
                  <Card className="p-4">
                    <div className="font-medium text-zinc-900">{item.title}</div>
                    <div className="text-sm text-zinc-600">{item.detail}</div>
                  </Card>
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
