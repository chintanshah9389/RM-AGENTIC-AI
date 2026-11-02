import type { ReactNode } from "react";
import { Loader2 } from "lucide-react";

type PageLoaderProps = {
  label?: string;
  className?: string;
};

/** Full-width loading state for page/query fetches. */
export function PageLoader({ label = "Loading...", className = "" }: PageLoaderProps) {
  return (
    <div
      className={`card flex flex-col items-center justify-center gap-3 px-6 py-16 text-slate-600 ${className}`}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <Loader2 className="animate-spin text-sky-600" size={28} />
      <p className="text-sm font-medium">{label}</p>
    </div>
  );
}

type InlineLoaderProps = {
  label?: string;
};

/** Compact spinner for buttons and inline actions. */
export function InlineLoader({ label }: InlineLoaderProps) {
  return (
    <span className="inline-flex items-center gap-2">
      <Loader2 className="animate-spin" size={16} />
      {label ? <span>{label}</span> : null}
    </span>
  );
}

type EmptyStateProps = {
  title?: string;
  message: string;
  hint?: string | null;
  action?: ReactNode;
};

/** Shared empty / no-data panel — used whenever DB/catalogue has no matching rows. */
export function EmptyState({
  title = "No data found",
  message,
  hint,
  action,
}: EmptyStateProps) {
  return (
    <div className="card border-rose-200 bg-rose-50 p-8 text-center space-y-3">
      <p className="text-lg font-semibold text-rose-900">{title}</p>
      <p className="text-sm text-rose-800 max-w-2xl mx-auto">{message}</p>
      {hint ? <p className="text-sm text-rose-700">{hint}</p> : null}
      {action ? <div className="pt-2">{action}</div> : null}
    </div>
  );
}
