"use client";

import { useEffect, useState } from "react";
import { CheckSquare } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { api, type PendingAction } from "@/lib/api/client";

const statusTone: Record<string, "warning" | "info" | "success" | "neutral" | "danger"> = {
  pending: "warning",
  approved: "info",
  executed: "success",
  rejected: "neutral",
  failed: "danger",
};

export default function ApprovalsPage() {
  const [actions, setActions] = useState<PendingAction[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    const { data, error } = await api.GET("/api/v1/approvals");
    if (error) {
      setError("Could not load the approval queue. Are you logged in?");
    } else {
      setActions(data ?? []);
    }
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function act(id: string, verb: "approve" | "reject" | "execute") {
    setBusyId(id);
    setError(null);
    const { error } = await api.POST(
      `/api/v1/approvals/{action_id}/${verb}` as "/api/v1/approvals/{action_id}/approve",
      { params: { path: { action_id: id } } }
    );
    if (error) {
      setError(
        verb === "execute"
          ? "Execute refused — the action must be approved first (this is the gate working)."
          : `Could not ${verb} the action.`
      );
    }
    setBusyId(null);
    await load();
  }

  return (
    <AppShell>
      <PageHeader
        title="Approval queue"
        description="You approve every outbound action before it happens."
        actions={
          <Button variant="secondary" onClick={load}>
            Refresh
          </Button>
        }
      />

      <Alert tone="success" className="mb-6">
        <strong>Nothing here has been sent.</strong> Every outbound action
        waits for you. Approve, then Execute — or Reject. The backend refuses
        to execute anything you have not explicitly approved.
      </Alert>

      {loading && (
        <div className="space-y-3">
          <Skeleton className="h-20 w-full rounded-xl" />
          <Skeleton className="h-20 w-full rounded-xl" />
          <Skeleton className="h-20 w-full rounded-xl" />
        </div>
      )}
      {error && (
        <Alert tone="warning" className="mb-4">
          {error}
        </Alert>
      )}

      {!loading && !error && actions.length === 0 && (
        <EmptyState icon={CheckSquare} title="Nothing pending" />
      )}

      <ul className="space-y-3">
        {actions.map((a) => (
          <li key={a.id}>
            <Card className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="font-medium text-zinc-900">{a.summary}</div>
                  <div className="text-xs text-zinc-500">
                    {a.type} · created {new Date(a.created_at).toLocaleString()}
                  </div>
                </div>
                <Badge tone={statusTone[a.status] ?? "neutral"}>{a.status}</Badge>
              </div>

              {a.error && <p className="mt-2 text-xs text-red-600">{a.error}</p>}

              <div className="mt-3 flex gap-2">
                <Button
                  onClick={() => act(a.id, "approve")}
                  disabled={busyId === a.id || a.status !== "pending"}
                >
                  Approve
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => act(a.id, "reject")}
                  disabled={busyId === a.id || a.status !== "pending"}
                >
                  Reject
                </Button>
                <Button
                  variant="success"
                  onClick={() => act(a.id, "execute")}
                  disabled={busyId === a.id || a.status !== "approved"}
                  title="Only enabled once approved — and the backend enforces this too."
                >
                  Execute
                </Button>
              </div>
            </Card>
          </li>
        ))}
      </ul>
    </AppShell>
  );
}
