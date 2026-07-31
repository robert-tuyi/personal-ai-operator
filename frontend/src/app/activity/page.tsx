"use client";

import { useEffect, useState } from "react";
import { History } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { api, type ActivityEntry } from "@/lib/api/client";

const eventTone: Record<string, "warning" | "info" | "success" | "neutral" | "danger"> = {
  proposed: "warning",
  approved: "info",
  executed: "success",
  rejected: "neutral",
  failed: "danger",
};

const eventLabel: Record<string, string> = {
  proposed: "Proposed",
  approved: "Approved",
  executed: "Executed",
  rejected: "Rejected",
  failed: "Failed",
};

export default function ActivityPage() {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    const { data, error } = await api.GET("/api/v1/activity");
    if (error) {
      setError("Could not load the activity log. Try refreshing.");
    } else {
      setEntries(data ?? []);
    }
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <AppShell>
      <PageHeader
        title="Activity log"
        description="A record of outbound actions proposed and their approval status."
        actions={
          <Button variant="secondary" onClick={load}>
            Refresh
          </Button>
        }
      />

      <Alert tone="info" className="mb-6">
        This shows what the app has actually tracked: proposed, approved,
        rejected, executed, and failed outbound actions. It doesn&apos;t yet
        track inbox reads or message classification — nothing in the product
        does that today.
      </Alert>

      {loading && (
        <div className="space-y-3">
          <Skeleton className="h-16 w-full rounded-xl" />
          <Skeleton className="h-16 w-full rounded-xl" />
          <Skeleton className="h-16 w-full rounded-xl" />
        </div>
      )}
      {error && (
        <Alert tone="warning" className="mb-4">
          {error}
        </Alert>
      )}

      {!loading && !error && entries.length === 0 && (
        <EmptyState icon={History} title="No activity yet" />
      )}

      <ul className="space-y-3">
        {entries.map((entry) => (
          <li key={entry.id}>
            <Card className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="break-words font-medium text-zinc-900">{entry.summary}</div>
                  <div className="text-xs text-zinc-500">
                    {entry.action_type} · {new Date(entry.created_at).toLocaleString()}
                  </div>
                </div>
                <Badge tone={eventTone[entry.event] ?? "neutral"}>
                  {eventLabel[entry.event] ?? entry.event}
                </Badge>
              </div>
              {entry.detail && (
                <p className="mt-2 break-words text-xs text-zinc-500">{entry.detail}</p>
              )}
            </Card>
          </li>
        ))}
      </ul>
    </AppShell>
  );
}
