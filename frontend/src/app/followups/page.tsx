"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { RefreshCw as RefreshCwIcon } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
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

      <Alert tone="success" className="mb-6">
        Each nudge is a <strong>draft only</strong> — queuing it creates a
        pending action in the approval queue, same as any other reply. Nothing
        sends until you approve and execute it there.
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
                <div className="font-medium text-zinc-900">{s.subject}</div>
                <div className="text-xs text-zinc-500">
                  Waiting on {s.to} · {s.days_waiting} days
                </div>

                <p className="mt-3 whitespace-pre-wrap rounded-lg bg-zinc-50 p-3 text-sm text-zinc-800">
                  {s.draft.body}
                </p>

                {!queued ? (
                  <Button
                    variant="success"
                    className="mt-3"
                    onClick={() => queue(s)}
                    disabled={busyId === s.thread_id}
                  >
                    Queue for sending
                  </Button>
                ) : (
                  <Alert tone="success" className="mt-3">
                    Queued. Nothing has been sent.{" "}
                    <Link href="/approvals" className="font-medium underline">
                      Review it in the approval queue →
                    </Link>
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
