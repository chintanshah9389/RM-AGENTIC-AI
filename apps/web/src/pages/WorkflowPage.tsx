import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import {
  ArrowRight,
  CheckCircle2,
  Circle,
  Loader2,
  ShieldAlert,
} from "lucide-react";
import { api } from "../api/client";
import { PageLoader } from "../components/PageLoader";
import { RmJourneyWizard } from "../components/RmJourneyWizard";
import { friendlyAgent, friendlyStatus } from "../lib/labels";
import { useToast } from "../components/toast/ToastProvider";
import { useQueryErrorToast } from "../hooks/useQueryToasts";

type Step = {
  id: string;
  agentName: string;
  status: string;
  summary?: string;
  processedRecords: number;
  durationMs?: number | null;
  error?: string | null;
};

function statusColor(status: string) {
  if (status === "COMPLETED") return "border-emerald-300 bg-emerald-50 text-emerald-800";
  if (status === "RUNNING") return "border-sky-300 bg-sky-50 text-sky-800";
  if (status === "WAITING_FOR_APPROVAL") return "border-amber-300 bg-amber-50 text-amber-800";
  if (status === "FAILED" || status === "BLOCKED") return "border-red-300 bg-red-50 text-red-800";
  return "border-slate-200 bg-slate-50 text-slate-600";
}

export function WorkflowPage() {
  const { campaignId, workflowId } = useParams();
  const toast = useToast();
  const announced = useRef<string>("");

  const { data: steps, isLoading, error: stepsError } = useQuery({
    queryKey: ["workflow-steps", workflowId],
    queryFn: () => api<Step[]>(`/workflows/${workflowId}/steps`),
    refetchInterval: 1200,
  });
  const { data: workflow, error: workflowError } = useQuery({
    queryKey: ["workflow", workflowId],
    queryFn: () =>
      api<{ status: string; currentStep?: string }>(`/workflows/${workflowId}`),
    refetchInterval: 1200,
  });

  const readyForReview =
    workflow?.status === "WAITING_FOR_APPROVAL" || workflow?.status === "COMPLETED";

  const { data: resultsPreview } = useQuery({
    queryKey: ["results-preview", campaignId, readyForReview],
    enabled: Boolean(campaignId && readyForReview),
    queryFn: () =>
      api<{
        count: number;
        noData?: boolean;
        noDataMessage?: string | null;
      }>(`/campaigns/${campaignId}/results`),
  });

  useQueryErrorToast(stepsError || workflowError, "Could not load workflow status");

  useEffect(() => {
    const status = workflow?.status;
    if (!status || announced.current === status) return;
    if (status === "FAILED") {
      announced.current = status;
      toast.error("Agent workflow failed. Check step details and try again.", "Workflow failed");
      return;
    }
    if (status !== "WAITING_FOR_APPROVAL" && status !== "COMPLETED") return;
    if (resultsPreview === undefined) return;
    announced.current = status;
    if (resultsPreview.noData || resultsPreview.count === 0) {
      toast.info(
        resultsPreview.noDataMessage ||
          "No data found for this request. Try a product that exists in the catalogue.",
        "No data found",
      );
    } else {
      toast.success("AI finished scoring. Review the customer shortlist.", "Workflow ready");
    }
  }, [workflow?.status, resultsPreview, toast]);

  const isRunning =
    !readyForReview && workflow?.status !== "FAILED" && workflow?.status !== "COMPLETED";

  const emptyResults = Boolean(
    readyForReview && (resultsPreview?.noData || resultsPreview?.count === 0),
  );

  return (
    <div className="space-y-5">
      <RmJourneyWizard
        current="workflow"
        campaignId={campaignId}
        workflowId={workflowId}
        allowNext={readyForReview}
      />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">AI is working on your campaign</h1>
          <p className="text-sm text-slate-500 mt-1">
            Each agent step below updates automatically. When it finishes, open the shortlist.
          </p>
        </div>
        {readyForReview ? (
          <Link to={`/campaigns/${campaignId}/results`} className="btn-primary">
            {emptyResults ? "View empty shortlist" : "Review customers"}
            <ArrowRight size={16} />
          </Link>
        ) : null}
      </div>

      <div className="card p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase text-slate-500">Overall status</p>
          <p className="font-semibold text-lg">{friendlyStatus(workflow?.status || "RUNNING")}</p>
        </div>
        <p className="text-sm text-slate-500">
          Current step: {friendlyAgent(workflow?.currentStep)}
        </p>
      </div>

      {isRunning ? (
        <div className="card border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900 flex items-center gap-3">
          <Loader2 className="animate-spin shrink-0" size={18} />
          <span>Agents are running — this page refreshes automatically.</span>
        </div>
      ) : null}

      {emptyResults ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-900 flex flex-wrap items-center justify-between gap-3">
          <span>
            {resultsPreview?.noDataMessage ||
              "No data found for this request. Nothing matched in the catalogue or shortlist."}
          </span>
          <Link to="/campaigns/new" className="btn-primary btn-sm">
            Try another request
          </Link>
        </div>
      ) : readyForReview ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900 flex flex-wrap items-center justify-between gap-3">
          <span>AI finished scoring and drafting. You can pick a customer now.</span>
          <Link to={`/campaigns/${campaignId}/results`} className="btn-success btn-sm">
            Go to customer shortlist <ArrowRight size={14} />
          </Link>
        </div>
      ) : null}

      {isLoading ? (
        <PageLoader label="Loading AI steps..." />
      ) : (
        <div className="space-y-3">
          {(steps || []).map((step) => (
            <div key={step.id} className={`card p-4 border ${statusColor(step.status)}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0">
                  {step.status === "COMPLETED" ? (
                    <CheckCircle2 className="mt-0.5 shrink-0" size={18} />
                  ) : step.status === "RUNNING" ? (
                    <Loader2 className="mt-0.5 animate-spin shrink-0" size={18} />
                  ) : step.status === "WAITING_FOR_APPROVAL" ? (
                    <ShieldAlert className="mt-0.5 shrink-0" size={18} />
                  ) : (
                    <Circle className="mt-0.5 shrink-0" size={18} />
                  )}
                  <div className="min-w-0">
                    <p className="font-semibold">{friendlyAgent(step.agentName)}</p>
                    <p className="text-sm mt-1 opacity-90 break-words">
                      {step.summary || "Waiting to start..."}
                    </p>
                  </div>
                </div>
                <div className="text-right text-xs space-y-1 shrink-0">
                  <p className="font-semibold">{friendlyStatus(step.status)}</p>
                  {step.durationMs != null ? <p>{step.durationMs} ms</p> : null}
                  {step.processedRecords ? <p>{step.processedRecords} records</p> : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
