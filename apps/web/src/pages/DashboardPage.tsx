import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowRight, Sparkles, Trash2, Users } from "lucide-react";
import { api } from "../api/client";
import { ConfirmDeleteModal } from "../components/ConfirmDeleteModal";
import { PageLoader } from "../components/PageLoader";
import { RmJourneyWizard } from "../components/RmJourneyWizard";
import { useToast } from "../components/toast/ToastProvider";
import { friendlyKpi, friendlyStatus } from "../lib/labels";
import { useEmptyDataToast, useQueryErrorToast } from "../hooks/useQueryToasts";

type Summary = {
  welcome: string;
  kpis: Record<string, number>;
  recentCampaigns: { id: string; name: string; status: string; createdAt?: string }[];
  recentWorkflows: { id: string; campaignId: string; status: string; currentStep?: string }[];
  disclaimer: string;
};

export function DashboardPage() {
  const qc = useQueryClient();
  const toast = useToast();
  const [pendingDelete, setPendingDelete] = useState<{ id: string; name: string } | null>(null);

  const { data, isLoading, error, isSuccess } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api<Summary>("/dashboard/summary"),
  });

  const deleteMutation = useMutation({
    mutationFn: (campaignId: string) =>
      api<{ id: string; deleted: boolean; name: string }>(`/campaigns/${campaignId}`, {
        method: "DELETE",
      }),
    onSuccess: (res) => {
      toast.success(`Deleted “${res.name}”.`, "Campaign removed");
      setPendingDelete(null);
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      qc.invalidateQueries({ queryKey: ["campaigns"] });
    },
    onError: (e: Error) => toast.error(e.message, "Delete failed"),
  });

  useQueryErrorToast(error, "Could not load dashboard");
  useEmptyDataToast(
    isSuccess,
    Boolean(data && (data.kpis.customersAnalysed ?? 0) === 0),
    "No customers in the database. Seed synthetic data before running campaigns.",
    "dashboard-empty-customers",
  );

  if (isLoading) return <PageLoader label="Loading your home screen..." />;
  if (error) return <p className="text-red-600">{(error as Error).message}</p>;
  if (!data) return null;

  const kpiEntries = Object.entries(data.kpis);

  return (
    <div className="space-y-6">
      <RmJourneyWizard current="dashboard" />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900">{data.welcome}</h1>
          <p className="text-sm text-amber-700 mt-1">{data.disclaimer}</p>
          <p className="text-sm text-slate-500 mt-1">
            Ready when you are — browse customers or start a new AI campaign.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/customers" className="btn-secondary">
            <Users size={16} /> Browse customers
          </Link>
          <Link to="/campaigns/new" className="btn-primary">
            <Sparkles size={16} /> Start AI campaign <ArrowRight size={16} />
          </Link>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-4">
        {kpiEntries.map(([key, value]) => (
          <div key={key} className="card p-4">
            <p className="text-xs uppercase tracking-wide text-slate-500">{friendlyKpi(key)}</p>
            <p className="mt-2 text-3xl font-bold text-navy-800">
              {Number(value).toLocaleString("en-IN")}
            </p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold">Your recent campaigns</h2>
            <Link to="/campaigns/new" className="text-sm font-semibold text-sky-700 hover:underline">
              New campaign
            </Link>
          </div>
          <div className="space-y-2">
            {data.recentCampaigns.length === 0 && (
              <div className="rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-500">
                No campaigns yet.
                <div className="mt-3">
                  <Link to="/campaigns/new" className="btn-primary btn-sm">
                    Create your first campaign
                  </Link>
                </div>
              </div>
            )}
            {data.recentCampaigns.map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between gap-2 rounded-lg border border-slate-100 px-3 py-2.5 hover:bg-slate-50"
              >
                <Link
                  to={`/campaigns/${c.id}/results`}
                  className="min-w-0 flex-1 flex items-center justify-between gap-2"
                >
                  <span className="text-sm font-medium truncate">{c.name}</span>
                  <span className="badge bg-slate-100 text-slate-700 shrink-0">
                    {friendlyStatus(c.status)}
                  </span>
                </Link>
                <button
                  type="button"
                  className="btn-ghost btn-sm text-rose-700 hover:bg-rose-50"
                  title="Delete campaign"
                  disabled={deleteMutation.isPending}
                  onClick={() => setPendingDelete({ id: c.id, name: c.name })}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        </div>
        <div className="card p-4">
          <h2 className="font-semibold mb-3">AI runs in progress</h2>
          <div className="space-y-2">
            {data.recentWorkflows.length === 0 && (
              <p className="text-sm text-slate-500">
                After you start a campaign, progress will show here.
              </p>
            )}
            {data.recentWorkflows.map((w) => (
              <Link
                key={w.id}
                to={`/campaigns/${w.campaignId}/workflow/${w.id}`}
                className="flex items-center justify-between rounded-lg border border-slate-100 px-3 py-2.5 hover:bg-slate-50"
              >
                <span className="text-sm">{w.currentStep || "AI workflow"}</span>
                <span className="badge bg-sky-50 text-sky-700">{friendlyStatus(w.status)}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <ConfirmDeleteModal
        open={Boolean(pendingDelete)}
        itemName={pendingDelete?.name}
        loading={deleteMutation.isPending}
        onCancel={() => {
          if (!deleteMutation.isPending) setPendingDelete(null);
        }}
        onConfirm={() => {
          if (pendingDelete) deleteMutation.mutate(pendingDelete.id);
        }}
      />
    </div>
  );
}
