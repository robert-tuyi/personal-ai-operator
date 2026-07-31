"use client";

import { useEffect, useState } from "react";
import { RefreshCw as RefreshCwIcon } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { LinkButton } from "@/components/ui/LinkButton";
import { PageHeader } from "@/components/ui/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { api, type FollowUpSuggestion } from "@/lib/api/client";

export default function FollowUpsPage() {
  const [suggestions, setSuggestions] = useState<FollowUpSuggestion[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [queuedIds, setQueuedIds] = useState<Set<string>>(new Set());

  async function load() {
    setLoading(true);
    setError(null);
    const { data, error } = await api.GET("/api/v1/followups");
    if (error) {
      setError("Could not load follow-up suggestions. Try refreshing.");
    } else {
      setSuggestions(data ?? []);
    }
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function queue(suggestion: FollowUpSuggestion) {
    setBusyId(suggestion.thread_id);
    setError(null);
    const { error } = await api.POST("/api/v1/drafts/send", {
      body: suggestion.draft,
    });
    if (error) {
      setError("Could not queue the nudge.");
    } else {
      setQueuedIds((prev) => new Set(prev).add(suggestion.thread_id));
    }
    setBusyId(null);
  }

  return (
    <AppShell>
      <PageHeader
        title="Follow-ups"
        description="Threads you sent the last message on, with no reply yet."
        actions={
          <Button variant="secondary" onClick={load}>
            Refresh
          </Button>
        }
      />

      <Alert tone="info" className="mb-6">
        <p className="mb-1">
          <strong>How this works:</strong> for each thread below, we&apos;ve
          drafted a nudge to send. Nothing happens on its own —
        </p>
        <ol className="ml-4 list-decimal space-y-0.5">
          <li>Read the suggested reply and edit it if you&apos;d like (in Compose).</li>
          <li>
            Click <strong>Queue for approval</strong> — this only adds it to
            your Approval queue, it does not send anything.
          </li>
          <li>
            Go to the <strong>Approval queue</strong> and click Approve, then
            Execute. That&apos;s the one step that actually sends it.
          </li>
        </ol>
      </Alert>

      {loading && (
        <div className="space-y-3">
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-24 w-full rounded-xl" />
          <Skeleton className="h-24 w-full rounded-xl" />
        </div>
      )}
      {error && (
        <Alert tone="warning" className="mb-4">
          {error}
        </Alert>
      )}

      {!loading && !error && suggestions.length === 0 && (
        <EmptyState
          icon={RefreshCwIcon}
          title="Nothing waiting on a reply right now"
        />
      )}

      <ul className="space-y-3">
        {suggestions.map((s) => {
          const queued = queuedIds.has(s.thread_id);
          return (
            <li key={s.thread_id}>
              <Card className="p-5">
                <div className="min-w-0">
                  <div className="break-words font-medium text-zinc-900">{s.subject}</div>
                  <div className="text-xs text-zinc-500">
                    Waiting on {s.to} · {s.days_waiting} days
                  </div>
                </div>

                <div className="mt-4">
                  <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-zinc-400">
                    Suggested reply
                  </div>
                  <p className="whitespace-pre-wrap break-words rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-sm text-zinc-800">
                    {s.draft.body}
                  </p>
                </div>

                {!queued ? (
                  <div className="mt-3 space-y-1.5">
                    <Button
                      variant="success"
                      onClick={() => queue(s)}
                      disabled={busyId === s.thread_id}
                    >
                      Queue for approval →
                    </Button>
                    <p className="text-xs text-zinc-500">
                      This does not send anything. You&apos;ll approve and
                      send it from the Approval queue.
                    </p>
                  </div>
                ) : (
                  <Alert tone="success" className="mt-3">
                    <p className="mb-2">
                      Queued. Nothing has been sent — one more step to go.
                    </p>
                    <LinkButton href="/approvals" variant="success">
                      Go approve &amp; send →
                    </LinkButton>
                  </Alert>
                )}
              </Card>
            </li>
          );
        })}
      </ul>
    </AppShell>
  );
}
