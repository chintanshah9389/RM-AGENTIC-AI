import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, CheckCircle2, Loader2, Sparkles, X } from "lucide-react";
import { api } from "../api/client";
import {
  AgentActivityLog,
  type AuditActivityEvent,
  type WorkflowStepActivity,
} from "./AgentActivityLog";
import { friendlyAgent, friendlyStatus } from "../lib/labels";

type BehindScenesSetupModalProps = {
  open: boolean;
  campaignId: string | null;
  workflowId: string | null;
  error?: string;
  bootstrapping?: boolean;
  onClose: () => void;
  onContinueToPreview: (opts: { ready: boolean; failed: boolean }) => void;
};

const SETUP_HINTS = [
  "Supervisor orchestrator boots the LangGraph pipeline",
  "Intent agent reads your request and calls catalogue tools",
  "Retrieval / scoring / compliance agents run on that intent",
  "Message drafts are prepared only for cleared contacts",
];

export function BehindScenesSetupModal({
  open,
  campaignId,
  workflowId,
  error,
  bootstrapping = false,
  onClose,
  onContinueToPreview,
}: BehindScenesSetupModalProps) {
  const enabled = open && Boolean(workflowId);

  const { data: steps } = useQuery({
    queryKey: ["modal-workflow-steps", workflowId],
    queryFn: () => api<WorkflowStepActivity[]>(`/workflows/${workflowId}/steps`),
    enabled,
    refetchInterval: 1000,
  });

  const { data: workflow } = useQuery({
    queryKey: ["modal-workflow", workflowId],
    queryFn: () =>
      api<{ status: string; currentStep?: string }>(`/workflows/${workflowId}`),
    enabled,
    refetchInterval: 1000,
  });

  const { data: auditEvents } = useQuery({
    queryKey: ["modal-workflow-audit", workflowId],
    queryFn: () =>
      api<AuditActivityEvent[]>(`/audit-events?workflow_run_id=${workflowId}&limit=100`),
    enabled,
    refetchInterval: 1000,
  });

  const ready =
    workflow?.status === "WAITING_FOR_APPROVAL" ||
    workflow?.status === "COMPLETED" ||
    workflow?.status === "FAILED";

  const isRunning = Boolean(workflowId) && !ready && workflow?.status !== "FAILED";

  const completedCount = useMemo(
    () => (steps || []).filter((s) => s.status === "COMPLETED" || s.status === "WAITING_FOR_APPROVAL").length,
    [steps],
  );

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/55 backdrop-blur-[2px]"
        aria-label="Close setup dialog backdrop"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="behind-scenes-title"
        className="relative z-10 flex max-h-[90vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
      >
        <div className="flex items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-sky-700">
              Behind the scenes
            </p>
            <h2 id="behind-scenes-title" className="font-display text-xl font-bold text-slate-900">
              AI campaign setup
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Watch agents, tools, and LLM calls while the shortlist is prepared.
            </p>
          </div>
          <button type="button" className="btn-ghost btn-sm" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4 overflow-auto px-5 py-4">
          <div className="rounded-xl border border-sky-100 bg-sky-50/80 px-4 py-3 text-sm text-sky-950">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="inline-flex items-center gap-2 font-medium">
                {bootstrapping || isRunning ? (
                  <Loader2 size={16} className="animate-spin text-sky-600" />
                ) : ready && workflow?.status !== "FAILED" ? (
                  <CheckCircle2 size={16} className="text-emerald-600" />
                ) : (
                  <Sparkles size={16} className="text-sky-600" />
                )}
                {bootstrapping
                  ? "Creating campaign and starting agents…"
                  : ready && workflow?.status === "FAILED"
                    ? "Workflow failed — check the log below"
                    : ready
                      ? "Setup complete — continue to shortlist preview"
                      : `Agents running · ${friendlyAgent(workflow?.currentStep)}`}
              </span>
              <span className="text-xs text-sky-800">
                {friendlyStatus(workflow?.status || (bootstrapping ? "RUNNING" : "PENDING"))}
                {steps ? ` · ${completedCount}/${steps.length} steps` : null}
              </span>
            </div>
          </div>

          <ul className="grid gap-2 sm:grid-cols-2">
            {SETUP_HINTS.map((hint, idx) => {
              const done = completedCount > idx + 1 || ready;
              return (
                <li
                  key={hint}
                  className={`rounded-lg border px-3 py-2 text-xs ${
                    done
                      ? "border-emerald-200 bg-emerald-50 text-emerald-900"
                      : "border-slate-200 bg-slate-50 text-slate-600"
                  }`}
                >
                  <span className="font-semibold">{done ? "Done · " : `${idx + 1}. `}</span>
                  {hint}
                </li>
              );
            })}
          </ul>

          {error ? <p className="text-sm text-rose-600">{error}</p> : null}

          <AgentActivityLog
            steps={steps}
            auditEvents={auditEvents}
            isRunning={bootstrapping || isRunning}
            maxHeightClass="max-h-64"
            emptyLabel={
              bootstrapping
                ? "Starting supervisor and creating workflow steps…"
                : "Waiting for the first agent to start…"
            }
          />

          {campaignId && workflowId ? (
            <p className="text-xs text-slate-500 font-mono">
              campaign {campaignId.slice(0, 8)}… · workflow {workflowId.slice(0, 8)}…
            </p>
          ) : null}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 bg-slate-50 px-5 py-4">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Stay on create form
          </button>
          <button
            type="button"
            className="btn-primary"
            disabled={!workflowId || bootstrapping}
            onClick={() =>
              onContinueToPreview({
                ready: Boolean(ready && workflow?.status !== "FAILED"),
                failed: workflow?.status === "FAILED",
              })
            }
          >
            {ready && workflow?.status !== "FAILED"
              ? "Continue to shortlist preview"
              : ready && workflow?.status === "FAILED"
                ? "Open workflow details"
                : "Open live preview"}
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
