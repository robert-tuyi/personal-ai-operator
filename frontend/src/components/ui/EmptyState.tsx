import type { LucideIcon } from "lucide-react";

export function EmptyState({
  icon: Icon,
  title,
  description,
}: {
  icon?: LucideIcon;
  title: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-zinc-200 bg-white/60 px-6 py-14 text-center">
      {Icon && <Icon className="mb-3 h-8 w-8 text-zinc-300" strokeWidth={1.5} />}
      <p className="text-sm font-medium text-zinc-600">{title}</p>
      {description && (
        <p className="mt-1 max-w-sm text-sm text-zinc-400">{description}</p>
      )}
    </div>
  );
}
