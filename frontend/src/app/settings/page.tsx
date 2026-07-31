"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, X } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, type UserSettings } from "@/lib/api/client";

const TONE_OPTIONS: { value: UserSettings["tone"]; label: string }[] = [
  { value: "formal", label: "Formal" },
  { value: "casual", label: "Casual" },
  { value: "direct", label: "Direct" },
];

const DEFAULT_SETTINGS: UserSettings = {
  work_hours_start: "09:00",
  work_hours_end: "17:00",
  timezone: "UTC",
  tone: "casual",
  vip_contacts: [],
  escalation_rules: [],
  onboarding_completed: false,
};

function TagList({
  items,
  placeholder,
  onChange,
}: {
  items: string[];
  placeholder: string;
  onChange: (items: string[]) => void;
}) {
  const [draft, setDraft] = useState("");

  function add() {
    const value = draft.trim();
    if (!value) return;
    onChange([...items, value]);
    setDraft("");
  }

  return (
    <div className="space-y-2">
      {items.map((item, i) => (
        <div
          key={i}
          className="flex items-center justify-between rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm"
        >
          <span className="min-w-0 break-words text-zinc-800">{item}</span>
          <button
            type="button"
            onClick={() => onChange(items.filter((_, j) => j !== i))}
            className="-m-2 shrink-0 p-2 text-zinc-400 hover:text-zinc-700"
            aria-label="Remove"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
      <div className="flex gap-2">
        <input
          className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200"
          placeholder={placeholder}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              add();
            }
          }}
        />
        <Button type="button" variant="secondary" onClick={add}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const router = useRouter();
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const [confirmingDisconnect, setConfirmingDisconnect] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [disconnectError, setDisconnectError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    const { data, error } = await api.GET("/api/v1/user-settings");
    if (error) {
      setError("Could not load your settings. Try refreshing.");
    } else if (data) {
      setSettings(data);
    }
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function save() {
    setSaving(true);
    setError(null);
    setSaved(false);
    const { data, error } = await api.PUT("/api/v1/user-settings", {
      body: settings,
    });
    if (error) {
      setError("Could not save your settings. Try again.");
    } else if (data) {
      setSettings(data);
      setSaved(true);
    }
    setSaving(false);
  }

  async function disconnectGoogle() {
    if (!confirmingDisconnect) {
      setConfirmingDisconnect(true);
      return;
    }
    setDisconnecting(true);
    setDisconnectError(null);
    const { error } = await api.POST("/api/v1/auth/disconnect");
    if (error) {
      setDisconnectError("Could not disconnect. Try again.");
      setDisconnecting(false);
      return;
    }
    router.push("/login");
    router.refresh();
  }

  return (
    <AppShell>
      <PageHeader
        title="Settings"
        description="Your working hours, timezone, tone, and contacts."
      />

      {loading && (
        <div className="space-y-4">
          <div className="h-40 animate-pulse rounded-xl bg-zinc-100" />
          <div className="h-40 animate-pulse rounded-xl bg-zinc-100" />
        </div>
      )}

      {error && (
        <Alert tone="warning" className="mb-4">
          {error}
        </Alert>
      )}

      {!loading && (
        <div className="space-y-6">
          <Card className="space-y-4 p-5">
            <h2 className="text-sm font-medium text-zinc-500">Google account</h2>

            <Alert tone="info">
              While this app is in Google&apos;s <strong>Testing</strong> mode,
              Google requires you to log in again about every 7 days. That&apos;s
              a limit Google places on unverified apps, not a problem with your
              account or a sign that anything went wrong — it goes away once
              Google verification is complete.
            </Alert>

            <div>
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  variant={confirmingDisconnect ? "danger" : "secondary"}
                  onClick={disconnectGoogle}
                  disabled={disconnecting}
                >
                  {disconnecting
                    ? "Disconnecting…"
                    : confirmingDisconnect
                      ? "Click again to confirm"
                      : "Disconnect Google account"}
                </Button>
                {confirmingDisconnect && !disconnecting && (
                  <button
                    type="button"
                    onClick={() => setConfirmingDisconnect(false)}
                    className="text-sm text-zinc-500 hover:text-zinc-700"
                  >
                    Cancel
                  </button>
                )}
              </div>
              <p className="mt-2 text-xs text-zinc-500">
                Revokes this app&apos;s access to your Gmail and Calendar and
                signs you out. Your settings and activity history are kept —
                nothing is deleted.
              </p>
              {disconnectError && (
                <Alert tone="warning" className="mt-2">
                  {disconnectError}
                </Alert>
              )}
            </div>
          </Card>

          <Card className="space-y-4 p-5">
            <h2 className="text-sm font-medium text-zinc-500">
              Working hours &amp; timezone
            </h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <label className="block text-sm">
                <span className="text-zinc-500">Start</span>
                <input
                  type="time"
                  className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200"
                  value={settings.work_hours_start}
                  onChange={(e) =>
                    setSettings({ ...settings, work_hours_start: e.target.value })
                  }
                />
              </label>
              <label className="block text-sm">
                <span className="text-zinc-500">End</span>
                <input
                  type="time"
                  className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200"
                  value={settings.work_hours_end}
                  onChange={(e) =>
                    setSettings({ ...settings, work_hours_end: e.target.value })
                  }
                />
              </label>
              <label className="block text-sm">
                <span className="text-zinc-500">Timezone (IANA name)</span>
                <input
                  className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200"
                  placeholder="Europe/Helsinki"
                  value={settings.timezone}
                  onChange={(e) =>
                    setSettings({ ...settings, timezone: e.target.value })
                  }
                />
              </label>
            </div>
          </Card>

          <Card className="space-y-4 p-5">
            <h2 className="text-sm font-medium text-zinc-500">Drafting tone</h2>
            <div className="flex flex-wrap gap-2">
              {TONE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setSettings({ ...settings, tone: opt.value })}
                  className={`min-h-[44px] rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
                    settings.tone === opt.value
                      ? "bg-zinc-900 text-white"
                      : "border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </Card>

          <Card className="space-y-4 p-5">
            <h2 className="text-sm font-medium text-zinc-500">VIP contacts</h2>
            <p className="text-xs text-zinc-400">
              Stored for future use — nothing reads this list yet.
            </p>
            <TagList
              items={settings.vip_contacts}
              placeholder="name@example.com"
              onChange={(vip_contacts) => setSettings({ ...settings, vip_contacts })}
            />
          </Card>

          <Card className="space-y-4 p-5">
            <h2 className="text-sm font-medium text-zinc-500">Escalation rules</h2>
            <p className="text-xs text-zinc-400">
              Stored for future use — nothing acts on these rules yet.
            </p>
            <TagList
              items={settings.escalation_rules}
              placeholder="e.g. Notify immediately if from a VIP contact"
              onChange={(escalation_rules) =>
                setSettings({ ...settings, escalation_rules })
              }
            />
          </Card>

          <div className="flex items-center gap-3">
            <Button onClick={save} disabled={saving}>
              {saving ? "Saving…" : "Save settings"}
            </Button>
            {saved && (
              <span className="text-sm text-emerald-600">Saved.</span>
            )}
          </div>
        </div>
      )}
    </AppShell>
  );
}
