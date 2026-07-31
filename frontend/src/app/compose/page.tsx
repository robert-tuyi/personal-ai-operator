"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, type DraftReply } from "@/lib/api/client";

// Split out so useSearchParams() (which opts the page out of static rendering) only
// affects this part — AppShell/PageHeader above it still render immediately.
function ComposeForm() {
  const searchParams = useSearchParams();
  // Prefilled when arriving from a brief item's "Compose reply" link — never the body,
  // so message content never ends up in the URL (browser history, server logs).
  const [sender, setSender] = useState(() => searchParams.get("sender") ?? "");
  const [subject, setSubject] = useState(() => searchParams.get("subject") ?? "");
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
      <Card className="space-y-3 p-5">
        <h2 className="text-sm font-medium text-zinc-500">Incoming message</h2>
        <input
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200"
          placeholder="From (sender)"
          value={sender}
          onChange={(e) => setSender(e.target.value)}
        />
        <input
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200"
          placeholder="Subject"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
        />
        <textarea
          className="h-32 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200"
          placeholder="Message body"
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
        <Button onClick={generate} disabled={busy}>
          {busy ? "Working…" : "Generate draft"}
        </Button>
      </Card>

      {error && (
        <Alert tone="danger" className="mt-4">
          {error}
        </Alert>
      )}

      {draft && (
        <Card className="mt-6 space-y-3 p-5">
          <h2 className="text-sm font-medium text-zinc-500">Proposed reply</h2>
          <div className="text-sm">
            <span className="text-zinc-500">To: </span>
            <span className="font-medium text-zinc-900">{draft.to}</span>
          </div>
          <label className="block text-sm">
            <span className="text-zinc-500">Subject</span>
            <input
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm font-medium focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200"
              value={draft.subject}
              onChange={(e) => setDraft({ ...draft, subject: e.target.value })}
              disabled={queued}
            />
          </label>
          <label className="block text-sm">
            <span className="text-zinc-500">Body</span>
            <textarea
              className="mt-1 h-40 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-800 focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200"
              value={draft.body}
              onChange={(e) => setDraft({ ...draft, body: e.target.value })}
              disabled={queued}
            />
          </label>

          {!queued ? (
            <div className="space-y-2 pt-1">
              <Button variant="success" onClick={queueForSending} disabled={busy}>
                Queue for sending
              </Button>
              <p className="text-xs text-zinc-500">
                This creates a <strong>pending action</strong> in the approval
                queue. It does <strong>not</strong> send the email — you approve
                and execute it yourself.
              </p>
            </div>
          ) : (
            <Alert tone="success">
              Queued. Nothing has been sent.{" "}
              <Link href="/approvals" className="font-medium underline">
                Review it in the approval queue →
              </Link>
            </Alert>
          )}
        </Card>
      )}
    </>
  );
}

export default function ComposePage() {
  return (
    <AppShell>
      <PageHeader
        title="Compose a reply"
        description="Draft a reply in your own voice, then review it before it's queued."
      />
      <Suspense fallback={null}>
        <ComposeForm />
      </Suspense>
    </AppShell>
  );
}
