"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
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

export default function OnboardingPage() {
  const router = useRouter();
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.GET("/api/v1/user-settings").then(({ data }) => {
      // Already onboarded (e.g. direct nav here after finishing) — nothing to do.
      if (data?.onboarding_completed) {
        router.replace("/brief");
        return;
      }
      if (data) setSettings(data);
      setLoading(false);
    });
  }, [router]);

  async function finish() {
    setSaving(true);
    setError(null);
    const { error } = await api.PUT("/api/v1/user-settings", {
      body: { ...settings, onboarding_completed: true },
    });
    if (error) {
      setError("Could not save your preferences. Try again.");
      setSaving(false);
      return;
    }
    router.replace("/brief");
  }

  if (loading) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6">
        <div className="h-64 w-full animate-pulse rounded-xl bg-zinc-100" />
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-8 px-6 py-12">
      <div className="space-y-3 text-center">
        <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-900 text-sm font-bold text-white">
          AI
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          Welcome
        </h1>
        <p className="text-sm leading-relaxed text-zinc-500">
          A couple of quick preferences before your first brief. You can
          change any of this later in Settings.
        </p>
      </div>

      <div className="space-y-5 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
        <div className="grid grid-cols-2 gap-4">
          <label className="block text-sm">
            <span className="text-zinc-500">Work starts</span>
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
            <span className="text-zinc-500">Work ends</span>
            <input
              type="time"
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200"
              value={settings.work_hours_end}
              onChange={(e) =>
                setSettings({ ...settings, work_hours_end: e.target.value })
              }
            />
          </label>
        </div>

        <label className="block text-sm">
          <span className="text-zinc-500">Timezone (IANA name)</span>
          <input
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-200"
            placeholder="Europe/Helsinki"
            value={settings.timezone}
            onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
          />
        </label>

        <div>
          <span className="text-sm text-zinc-500">Drafting tone</span>
          <div className="mt-1 flex gap-2">
            {TONE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setSettings({ ...settings, tone: opt.value })}
                className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  settings.tone === opt.value
                    ? "bg-zinc-900 text-white"
                    : "border border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-50"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && <Alert tone="warning">{error}</Alert>}

      <Button onClick={finish} disabled={saving}>
        {saving ? "Getting things ready…" : "Get started"}
      </Button>
    </main>
  );
}
