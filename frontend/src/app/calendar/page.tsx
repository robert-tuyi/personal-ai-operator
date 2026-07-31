"use client";

import { useEffect, useState } from "react";
import { CalendarDays, Clock } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "@/components/ui/PageHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { api, type CalendarEvent, type CalendarView } from "@/lib/api/client";

function isAllDay(event: CalendarEvent): boolean {
  return !event.start.includes("T");
}

function formatEventTime(event: CalendarEvent): string {
  if (isAllDay(event)) return "All day";
  const start = new Date(event.start);
  const end = new Date(event.end);
  const time = (d: Date) =>
    d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return `${time(start)} – ${time(end)}`;
}

function formatEventDate(event: CalendarEvent): string {
  const start = new Date(event.start);
  return start.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function EventRow({ event, showDate }: { event: CalendarEvent; showDate?: boolean }) {
  return (
    <li className="flex items-center gap-4 px-5 py-4">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-zinc-100 text-zinc-500">
        <Clock className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium text-zinc-900">{event.title}</div>
        <div className="text-sm text-zinc-500">
          {showDate && <span>{formatEventDate(event)} · </span>}
          {formatEventTime(event)}
        </div>
      </div>
    </li>
  );
}

export default function CalendarPage() {
  const [view, setView] = useState<CalendarView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    const { data, error } = await api.GET("/api/v1/calendar");
    if (error) {
      setError("Could not load your calendar. Are you logged in?");
    } else {
      setView(data ?? null);
    }
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  const today = view?.today ?? [];
  const upcoming = view?.upcoming ?? [];

  return (
    <AppShell>
      <PageHeader
        title="Calendar"
        description="Today's schedule and what's coming up next."
        actions={
          <Button variant="secondary" onClick={load}>
            Refresh
          </Button>
        }
      />

      {loading && (
        <div className="space-y-8">
          <section>
            <Skeleton className="mb-3 h-4 w-16" />
            <div className="space-y-px overflow-hidden rounded-xl">
              <Skeleton className="h-16 w-full rounded-none" />
              <Skeleton className="h-16 w-full rounded-none" />
            </div>
          </section>
          <section>
            <Skeleton className="mb-3 h-4 w-20" />
            <div className="space-y-px overflow-hidden rounded-xl">
              <Skeleton className="h-16 w-full rounded-none" />
              <Skeleton className="h-16 w-full rounded-none" />
              <Skeleton className="h-16 w-full rounded-none" />
            </div>
          </section>
        </div>
      )}
      {error && (
        <Alert tone="warning" className="mb-6">
          {error}
        </Alert>
      )}

      {!loading && !error && (
        <div className="space-y-8">
          <section>
            <h2 className="mb-3 text-sm font-medium text-zinc-500">Today</h2>
            {today.length === 0 ? (
              <EmptyState
                icon={CalendarDays}
                title="Nothing on your calendar today"
              />
            ) : (
              <Card>
                <ul className="divide-y divide-zinc-100">
                  {today.map((event) => (
                    <EventRow key={event.id} event={event} />
                  ))}
                </ul>
              </Card>
            )}
          </section>

          <section>
            <h2 className="mb-3 text-sm font-medium text-zinc-500">
              Upcoming
            </h2>
            {upcoming.length === 0 ? (
              <EmptyState
                icon={CalendarDays}
                title="Nothing on the calendar for the next week"
              />
            ) : (
              <Card>
                <ul className="divide-y divide-zinc-100">
                  {upcoming.map((event) => (
                    <EventRow key={event.id} event={event} showDate />
                  ))}
                </ul>
              </Card>
            )}
          </section>
        </div>
      )}
    </AppShell>
  );
}
