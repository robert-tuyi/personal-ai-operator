"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Nav } from "@/components/Nav";
import { api, type DailyBrief } from "@/lib/api/client";

// Map markdown elements to Tailwind classes so the model's formatting renders cleanly
// without depending on the typography plugin.
const markdownComponents = {
  p: (props: React.HTMLAttributes<HTMLParagraphElement>) => (
    <p className="mb-3 text-slate-700 last:mb-0" {...props} />
  ),
  ul: (props: React.HTMLAttributes<HTMLUListElement>) => (
    <ul className="mb-3 list-disc space-y-1 pl-5 text-slate-700 last:mb-0" {...props} />
  ),
  ol: (props: React.HTMLAttributes<HTMLOListElement>) => (
    <ol className="mb-3 list-decimal space-y-1 pl-5 text-slate-700 last:mb-0" {...props} />
  ),
  h1: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h2 className="mb-2 mt-4 text-lg font-semibold text-slate-900 first:mt-0" {...props} />
  ),
  h2: (props: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h3 className="mb-2 mt-4 font-semibold text-slate-900 first:mt-0" {...props} />
  ),
  strong: (props: React.HTMLAttributes<HTMLElement>) => (
    <strong className="font-semibold text-slate-900" {...props} />
  ),
  a: (props: React.AnchorHTMLAttributes<HTMLAnchorElement>) => (
    <a className="text-blue-600 underline" {...props} />
  ),
};

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
            <div className="rounded-lg border border-slate-200 bg-white p-4 text-slate-700">
              {brief.summary ? (
                <ReactMarkdown components={markdownComponents}>
                  {brief.summary}
                </ReactMarkdown>
              ) : (
                "Nothing notable today."
              )}
            </div>

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
