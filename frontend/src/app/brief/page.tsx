"use client";

import { useEffect, useState } from "react";
import { Nav } from "@/components/Nav";
import { api, type DailyBrief } from "@/lib/api/client";

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
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Daily brief</h1>
          <button
            onClick={load}
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>

        {loading && <p className="text-slate-500">Loading…</p>}
        {error && (
          <p className="rounded-md bg-amber-50 p-4 text-sm text-amber-800">
            {error}
          </p>
        )}

        {brief && !loading && (
          <div className="space-y-6">
            <p className="rounded-lg border border-slate-200 bg-white p-4 text-slate-700">
              {brief.summary || "Nothing notable today."}
            </p>

            <ul className="space-y-3">
              {(brief.items ?? []).map((item, i) => (
                <li
                  key={i}
                  className="rounded-lg border border-slate-200 bg-white p-4"
                >
                  <div className="font-medium text-slate-900">{item.title}</div>
                  <div className="text-sm text-slate-600">{item.detail}</div>
                </li>
              ))}
              {(brief.items ?? []).length === 0 && (
                <li className="text-sm text-slate-400">No items.</li>
              )}
            </ul>
          </div>
        )}
      </main>
    </>
  );
}
