"use client";

import { useState } from "react";
import Link from "next/link";
import { Nav } from "@/components/Nav";
import { api, type DraftReply } from "@/lib/api/client";

export default function ComposePage() {
  const [sender, setSender] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const [draft, setDraft] = useState<DraftReply | null>(null);
  const [queued, setQueued] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setBusy(true);
    setError(null);
    setQueued(false);
    const { data, error } = await api.POST("/api/v1/drafts", {
      body: { id: "", sender, subject, body },
    });
    if (error) {
      setError("Could not generate a draft.");
    } else {
      setDraft(data ?? null);
    }
    setBusy(false);
  }

  async function queueForSending() {
    if (!draft) return;
    setBusy(true);
    setError(null);
    const { error } = await api.POST("/api/v1/drafts/send", { body: draft });
    if (error) {
      setError("Could not queue the draft.");
    } else {
      setQueued(true);
    }
    setBusy(false);
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-8">
        <h1 className="mb-6 text-2xl font-semibold">Compose a reply</h1>

        <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-medium text-slate-500">
            Incoming message
          </h2>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="From (sender)"
            value={sender}
            onChange={(e) => setSender(e.target.value)}
          />
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
          />
          <textarea
            className="h-32 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Message body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
          <button
            onClick={generate}
            disabled={busy}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {busy ? "Working…" : "Generate draft"}
          </button>
        </section>

        {error && (
          <p className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}

        {draft && (
          <section className="mt-6 space-y-3 rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="text-sm font-medium text-slate-500">
              Proposed reply
            </h2>
            <div className="text-sm">
              <span className="text-slate-500">To: </span>
              <span className="font-medium">{draft.to}</span>
            </div>
            <label className="block text-sm">
              <span className="text-slate-500">Subject</span>
              <input
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm font-medium"
                value={draft.subject}
                onChange={(e) =>
                  setDraft({ ...draft, subject: e.target.value })
                }
                disabled={queued}
              />
            </label>
            <label className="block text-sm">
              <span className="text-slate-500">Body</span>
              <textarea
                className="mt-1 h-40 w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-800"
                value={draft.body}
                onChange={(e) => setDraft({ ...draft, body: e.target.value })}
                disabled={queued}
              />
            </label>

            {!queued ? (
              <div className="space-y-2">
                <button
                  onClick={queueForSending}
                  disabled={busy}
                  className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
                >
                  Queue for sending
                </button>
                <p className="text-xs text-slate-500">
                  This creates a <strong>pending action</strong> in the approval
                  queue. It does <strong>not</strong> send the email — you approve
                  and execute it yourself.
                </p>
              </div>
            ) : (
              <div className="rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">
                Queued. Nothing has been sent.{" "}
                <Link href="/approvals" className="font-medium underline">
                  Review it in the approval queue →
                </Link>
              </div>
            )}
          </section>
        )}
      </main>
    </>
  );
}
