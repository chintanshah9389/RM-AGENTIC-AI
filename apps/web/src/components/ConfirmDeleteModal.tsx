import { useEffect } from "react";
import { AlertTriangle, Loader2, Trash2, X } from "lucide-react";

type ConfirmDeleteModalProps = {
  open: boolean;
  title?: string;
  itemName?: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  loading?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
};

export function ConfirmDeleteModal({
  open,
  title = "Delete campaign?",
  itemName,
  message = "This permanently removes the shortlist, message drafts, approvals, and workflow history for this campaign.",
  confirmLabel = "Delete campaign",
  cancelLabel = "Keep campaign",
  loading = false,
  onCancel,
  onConfirm,
}: ConfirmDeleteModalProps) {
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape" && !loading) onCancel();
    }
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [open, loading, onCancel]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/55 backdrop-blur-[2px]"
        aria-label="Close delete dialog"
        disabled={loading}
        onClick={() => {
          if (!loading) onCancel();
        }}
      />
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="delete-campaign-title"
        aria-describedby="delete-campaign-desc"
        className="relative z-10 w-full max-w-md overflow-hidden rounded-2xl border border-rose-100 bg-white shadow-2xl"
      >
        <div className="flex items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 rounded-full bg-rose-50 p-2 text-rose-700">
              <AlertTriangle size={18} />
            </div>
            <div>
              <h2 id="delete-campaign-title" className="font-display text-lg font-bold text-slate-900">
                {title}
              </h2>
              {itemName ? (
                <p className="mt-1 text-sm font-semibold text-slate-800">“{itemName}”</p>
              ) : null}
            </div>
          </div>
          <button
            type="button"
            className="btn-ghost btn-sm"
            disabled={loading}
            onClick={onCancel}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-3 px-5 py-4">
          <p id="delete-campaign-desc" className="text-sm text-slate-600">
            {message}
          </p>
          <ul className="rounded-xl border border-rose-100 bg-rose-50/70 px-3 py-2.5 text-xs text-rose-900 space-y-1">
            <li>Customer shortlist and scores</li>
            <li>WhatsApp drafts and approval history</li>
            <li>AI workflow steps for this campaign</li>
          </ul>
          <p className="text-xs text-slate-500">Customers and product catalogue data are kept.</p>
        </div>

        <div className="flex flex-wrap items-center justify-end gap-2 border-t border-slate-100 bg-slate-50 px-5 py-4">
          <button type="button" className="btn-secondary" disabled={loading} onClick={onCancel}>
            {cancelLabel}
          </button>
          <button
            type="button"
            className="btn-danger"
            disabled={loading}
            onClick={onConfirm}
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Deleting…
              </>
            ) : (
              <>
                <Trash2 size={16} />
                {confirmLabel}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
