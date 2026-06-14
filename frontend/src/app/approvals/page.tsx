"use client";

import { useEffect, useState } from "react";
import { Nav } from "@/components/Nav";
import { api, type PendingAction } from "@/lib/api/client";

const statusStyles: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  approved: "bg-blue-100 text-blue-800",
  executed: "bg-emerald-100 text-emerald-800",
  rejected: "bg-slate-200 text-slate-600",
  failed: "bg-red-100 text-red-700",
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

  async function act(
    id: string,
    verb: "approve" | "reject" | "execute"
  ) {
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
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-2 flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Approval queue</h1>
          <button
            onClick={load}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>

        <p className="mb-6 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
          <strong>Nothing here has been sent.</strong> Every outbound action waits
          for you. Approve, then Execute — or Reject. The backend refuses to
          execute anything you have not explicitly approved.
        </p>

        {loading && <p className="text-slate-500">Loading…</p>}
        {error && (
          <p className="mb-4 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
            {error}
          </p>
        )}

        {!loading && actions.length === 0 && (
          <p className="text-sm text-slate-400">Nothing pending.</p>
        )}

        <ul className="space-y-3">
          {actions.map((a) => (
            <li
              key={a.id}
              className="rounded-lg border border-slate-200 bg-white p-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="font-medium text-slate-900">{a.summary}</div>
                  <div className="text-xs text-slate-500">
                    {a.type} · created{" "}
                    {new Date(a.created_at).toLocaleString()}
                  </div>
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    statusStyles[a.status] ?? "bg-slate-100 text-slate-600"
                  }`}
                >
                  {a.status}
                </span>
              </div>

              {a.error && (
                <p className="mt-2 text-xs text-red-600">{a.error}</p>
              )}

              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => act(a.id, "approve")}
                  disabled={busyId === a.id || a.status !== "pending"}
                  className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-40"
                >
                  Approve
                </button>
                <button
                  onClick={() => act(a.id, "reject")}
                  disabled={busyId === a.id || a.status !== "pending"}
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-40"
                >
                  Reject
                </button>
                <button
                  onClick={() => act(a.id, "execute")}
                  disabled={busyId === a.id || a.status !== "approved"}
                  className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-40"
                  title="Only enabled once approved — and the backend enforces this too."
                >
                  Execute
                </button>
              </div>
            </li>
          ))}
        </ul>
      </main>
    </>
  );
}
