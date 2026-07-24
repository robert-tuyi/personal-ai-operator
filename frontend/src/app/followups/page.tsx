"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Nav } from "@/components/Nav";
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
      setError("Could not load follow-up suggestions. Are you logged in?");
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
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-2 flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Follow-ups</h1>
          <button
            onClick={load}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>

        <p className="mb-6 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
          Threads you sent the last message on, with no reply yet. Each nudge is
          a <strong>draft only</strong> — queuing it creates a pending action in
          the approval queue, same as any other reply. Nothing sends until you
          approve and execute it there.
        </p>

        {loading && <p className="text-slate-500">Loading…</p>}
        {error && (
          <p className="mb-4 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
            {error}
          </p>
        )}

        {!loading && suggestions.length === 0 && (
          <p className="text-sm text-slate-400">
            Nothing waiting on a reply right now.
          </p>
        )}

        <ul className="space-y-3">
          {suggestions.map((s) => {
            const queued = queuedIds.has(s.thread_id);
            return (
              <li
                key={s.thread_id}
                className="rounded-lg border border-slate-200 bg-white p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="font-medium text-slate-900">
                      {s.subject}
                    </div>
                    <div className="text-xs text-slate-500">
                      Waiting on {s.to} · {s.days_waiting} days
                    </div>
                  </div>
                </div>

                <pre className="mt-3 whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-sm text-slate-800">
                  {s.draft.body}
                </pre>

                {!queued ? (
                  <button
                    onClick={() => queue(s)}
                    disabled={busyId === s.thread_id}
                    className="mt-3 rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-40"
                  >
                    Queue for sending
                  </button>
                ) : (
                  <div className="mt-3 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">
                    Queued. Nothing has been sent.{" "}
                    <Link href="/approvals" className="font-medium underline">
                      Review it in the approval queue →
                    </Link>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </main>
    </>
  );
}
