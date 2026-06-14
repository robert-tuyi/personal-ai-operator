import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-8 px-6 text-center">
      <div className="space-y-3">
        <h1 className="text-3xl font-semibold text-slate-900">
          Personal AI Operator
        </h1>
        <p className="text-slate-600">
          A daily brief and style-matched draft replies for your inbox. The core
          promise: <strong>nothing is ever sent without your explicit approval.</strong>
        </p>
      </div>

      <Link
        href="/login"
        className="rounded-md bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-700"
      >
        Get started
      </Link>

      <div className="grid w-full gap-3 sm:grid-cols-3">
        <Link
          href="/brief"
          className="rounded-lg border border-slate-200 bg-white p-4 text-left hover:border-slate-300"
        >
          <div className="font-medium">Daily brief</div>
          <div className="text-sm text-slate-500">A quick read on today.</div>
        </Link>
        <Link
          href="/compose"
          className="rounded-lg border border-slate-200 bg-white p-4 text-left hover:border-slate-300"
        >
          <div className="font-medium">Compose</div>
          <div className="text-sm text-slate-500">Draft a reply.</div>
        </Link>
        <Link
          href="/approvals"
          className="rounded-lg border border-slate-200 bg-white p-4 text-left hover:border-slate-300"
        >
          <div className="font-medium">Approval queue</div>
          <div className="text-sm text-slate-500">You approve every send.</div>
        </Link>
      </div>
    </main>
  );
}
