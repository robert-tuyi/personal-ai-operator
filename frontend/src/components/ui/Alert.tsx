import type { ReactNode } from "react";

type Tone = "info" | "success" | "warning" | "danger";

const toneClasses: Record<Tone, string> = {
  info: "border-blue-200 bg-blue-50 text-blue-800",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  warning: "border-amber-200 bg-amber-50 text-amber-800",
  danger: "border-red-200 bg-red-50 text-red-700",
};

export function Alert({
  tone = "info",
  children,
  className = "",
}: {
  tone?: Tone;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${toneClasses[tone]} ${className}`}>
      {children}
    </div>
  );
}
