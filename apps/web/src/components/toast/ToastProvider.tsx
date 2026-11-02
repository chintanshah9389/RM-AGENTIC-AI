import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { CheckCircle2, Info, X, XCircle } from "lucide-react";

export type ToastKind = "success" | "error" | "info";

export type ToastInput = {
  title?: string;
  message: string;
  kind?: ToastKind;
  durationMs?: number;
};

type ToastItem = {
  id: string;
  title: string;
  message: string;
  kind: ToastKind;
};

type ToastContextValue = {
  push: (input: ToastInput) => void;
  success: (message: string, title?: string) => void;
  error: (message: string, title?: string) => void;
  info: (message: string, title?: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

let externalPush: ((input: ToastInput) => void) | null = null;

/** Imperative helper for non-React modules (e.g. api client). */
export const toast = {
  push: (input: ToastInput) => externalPush?.(input),
  success: (message: string, title = "Success") =>
    externalPush?.({ kind: "success", title, message }),
  error: (message: string, title = "Something went wrong") =>
    externalPush?.({ kind: "error", title, message }),
  info: (message: string, title = "Notice") =>
    externalPush?.({ kind: "info", title, message }),
};

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback(
    (input: ToastInput) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const kind = input.kind || "info";
      const title =
        input.title ||
        (kind === "success" ? "Success" : kind === "error" ? "Error" : "Notice");
      const item: ToastItem = {
        id,
        kind,
        title,
        message: input.message,
      };
      setItems((prev) => [...prev, item].slice(-5));
      const duration = input.durationMs ?? (kind === "error" ? 5500 : 3500);
      window.setTimeout(() => dismiss(id), duration);
    },
    [dismiss],
  );

  externalPush = push;

  const value = useMemo<ToastContextValue>(
    () => ({
      push,
      success: (message, title = "Success") => push({ kind: "success", title, message }),
      error: (message, title = "Something went wrong") =>
        push({ kind: "error", title, message }),
      info: (message, title = "Notice") => push({ kind: "info", title, message }),
    }),
    [push],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed right-4 top-4 z-[100] flex w-[min(92vw,24rem)] flex-col gap-2"
        aria-live="polite"
      >
        {items.map((item) => (
          <div
            key={item.id}
            className={`pointer-events-auto flex gap-3 rounded-xl border px-4 py-3 shadow-lg ${
              item.kind === "success"
                ? "border-emerald-200 bg-emerald-50 text-emerald-950"
                : item.kind === "error"
                  ? "border-rose-200 bg-rose-50 text-rose-950"
                  : "border-sky-200 bg-sky-50 text-sky-950"
            }`}
          >
            <span className="mt-0.5 shrink-0">
              {item.kind === "success" ? (
                <CheckCircle2 size={18} className="text-emerald-600" />
              ) : item.kind === "error" ? (
                <XCircle size={18} className="text-rose-600" />
              ) : (
                <Info size={18} className="text-sky-600" />
              )}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold">{item.title}</p>
              <p className="mt-0.5 text-sm leading-snug opacity-90">{item.message}</p>
            </div>
            <button
              type="button"
              className="shrink-0 rounded-md p-1 opacity-60 hover:bg-black/5 hover:opacity-100"
              onClick={() => dismiss(item.id)}
              aria-label="Dismiss"
            >
              <X size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
