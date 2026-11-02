import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Home, Trash2 } from "lucide-react";
import { api } from "../api/client";
import { ConfirmDeleteModal } from "../components/ConfirmDeleteModal";
import { EmptyState, PageLoader } from "../components/PageLoader";
import { RmJourneyWizard } from "../components/RmJourneyWizard";
import { useToast } from "../components/toast/ToastProvider";
import { actionLabelForResult, friendlyStatus } from "../lib/labels";
import { useEmptyDataToast, useQueryErrorToast } from "../hooks/useQueryToasts";

type ResultRow = {
  customerId: string;
  customerName: string;
  segment: string;
  city: string;
  monthlyIncome: number;
  valueScore: number;
  propensityScore: number;
  recommendedProduct?: string;
  eligibility?: string;
  compliance?: string;
  contactAllowed: boolean;
  messageStatus?: string;
  messageId?: string;
  scenarioTag?: string;
};

type ResultsPayload = {
  results: ResultRow[];
  disclaimer: string;
  count: number;
  noData?: boolean;
  noDataMessage?: string | null;
  productCategory?: string | null;
  requestedProductCategory?: string | null;
  productCategoryResolved?: boolean | null;
  availableProductCategories?: string[];
};

function prettyCategory(value?: string | null) {
  return (value || "").replaceAll("_", " ");
}

export function ResultsPage() {
  const { campaignId } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [propensity, setPropensity] = useState("");
  const [compliance, setCompliance] = useState("");
  const [deleteOpen, setDeleteOpen] = useState(false);

  const query = useMemo(() => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (propensity) params.set("propensity", propensity);
    if (compliance) params.set("compliance", compliance);
    const qs = params.toString();
    return `/campaigns/${campaignId}/results${qs ? `?${qs}` : ""}`;
  }, [campaignId, search, propensity, compliance]);

  const { data, isLoading, isFetching, error, isSuccess } = useQuery({
    queryKey: ["results", query],
    queryFn: () => api<ResultsPayload>(query),
  });

  const deleteMutation = useMutation({
    mutationFn: () =>
      api<{ id: string; deleted: boolean; name: string }>(`/campaigns/${campaignId}`, {
        method: "DELETE",
      }),
    onSuccess: (res) => {
      toast.success(`Deleted “${res.name}”.`, "Campaign removed");
      setDeleteOpen(false);
      qc.invalidateQueries({ queryKey: ["dashboard"] });
      navigate("/");
    },
    onError: (e: Error) => toast.error(e.message, "Delete failed"),
  });

  const requestedLabel = prettyCategory(
    data?.requestedProductCategory || data?.productCategory,
  );
  const emptyMessage =
    data?.noDataMessage ||
    (requestedLabel
      ? `No data found for ${requestedLabel}. Nothing matched in the product catalogue or shortlist.`
      : "No data found. Nothing matched in the product catalogue or shortlist.");

  useQueryErrorToast(error, "Could not load campaign results");
  useEmptyDataToast(
    isSuccess,
    Boolean(data?.noData || (data && data.count === 0)),
    emptyMessage,
    `results-empty-${campaignId}-${data?.requestedProductCategory || data?.productCategory || "none"}`,
  );

  const actionable = (data?.results || []).filter((r) => r.contactAllowed && r.messageId).length;
  const showEmpty = !isLoading && Boolean(data?.noData || (data && data.count === 0));
  const availableHint =
    (data?.availableProductCategories || []).length > 0
      ? `Available in catalogue: ${(data?.availableProductCategories || [])
          .map((c) => prettyCategory(c))
          .join(", ")}`
      : null;

  return (
    <div className="space-y-4">
      <RmJourneyWizard current="results" campaignId={campaignId} />
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Customer shortlist</h1>
          <p className="text-sm text-amber-700">
            {data?.disclaimer || "POC Environment - Synthetic Data"}
          </p>
          <p className="text-sm text-slate-500 mt-1">
            Open a customer who is cleared to contact, then approve the WhatsApp draft.
          </p>
          {requestedLabel ? (
            <p className="text-sm text-slate-600 mt-1">
              Requested product: <span className="font-semibold">{requestedLabel}</span>
              {data?.productCategoryResolved === false ? (
                <span className="ml-2 badge bg-rose-50 text-rose-700">Not in catalogue</span>
              ) : null}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {data && !showEmpty && !isLoading ? (
            <p className="text-sm font-medium text-slate-700">
              {data.count} in shortlist · {actionable} ready for you
              {isFetching ? <span className="ml-2 text-slate-400">Updating…</span> : null}
            </p>
          ) : null}
          <Link to="/" className="btn-secondary btn-sm">
            <Home size={14} />
            Back to home
          </Link>
          {campaignId ? (
            <button
              type="button"
              className="btn-secondary btn-sm text-rose-700 border-rose-200 hover:bg-rose-50"
              disabled={deleteMutation.isPending}
              onClick={() => setDeleteOpen(true)}
            >
              <Trash2 size={14} />
              Delete campaign
            </button>
          ) : null}
        </div>
      </div>

      <ConfirmDeleteModal
        open={deleteOpen}
        itemName={requestedLabel ? `${requestedLabel} campaign` : "This campaign"}
        loading={deleteMutation.isPending}
        onCancel={() => {
          if (!deleteMutation.isPending) setDeleteOpen(false);
        }}
        onConfirm={() => {
          if (campaignId) deleteMutation.mutate();
        }}
      />

      {isLoading ? (
        <PageLoader label="Loading shortlist..." />
      ) : error ? (
        <EmptyState
          title="Could not load results"
          message={(error as Error).message}
          action={
            <Link to="/campaigns/new" className="btn-primary">
              Create another campaign
            </Link>
          }
        />
      ) : showEmpty ? (
        <EmptyState
          title="No data found"
          message={emptyMessage}
          hint={availableHint}
          action={
            <Link to="/campaigns/new" className="btn-primary">
              Try another campaign request
            </Link>
          }
        />
      ) : (
        <>
          <div className="card p-4 grid md:grid-cols-3 gap-3">
            <label className="text-sm">
              <span className="font-medium text-slate-600">Search by name</span>
              <input
                className="field"
                placeholder="Type a customer name"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </label>
            <label className="text-sm">
              <span className="font-medium text-slate-600">Conversion chance</span>
              <select
                className="field"
                value={propensity}
                onChange={(e) => setPropensity(e.target.value)}
              >
                <option value="">All levels</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </label>
            <label className="text-sm">
              <span className="font-medium text-slate-600">Contact permission</span>
              <select
                className="field"
                value={compliance}
                onChange={(e) => setCompliance(e.target.value)}
              >
                <option value="">All</option>
                <option value="PASSED">Cleared to contact</option>
                <option value="BLOCKED">Blocked</option>
              </select>
            </label>
          </div>

          <div className={`card overflow-auto relative ${isFetching ? "opacity-70" : ""}`}>
            {isFetching ? (
              <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/50">
                <PageLoader label="Updating shortlist..." className="border-0 shadow-none bg-transparent py-6" />
              </div>
            ) : null}
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-3 py-3">Customer</th>
                  <th className="px-3 py-3">Segment</th>
                  <th className="px-3 py-3">City</th>
                  <th className="px-3 py-3">Income</th>
                  <th className="px-3 py-3">Value</th>
                  <th className="px-3 py-3">Conversion</th>
                  <th className="px-3 py-3">Suggested product</th>
                  <th className="px-3 py-3">Eligible?</th>
                  <th className="px-3 py-3">Can contact?</th>
                  <th className="px-3 py-3">Message</th>
                  <th className="px-3 py-3">Your next action</th>
                </tr>
              </thead>
              <tbody>
                {(data?.results || []).map((r) => (
                  <tr key={r.customerId} className="border-t border-slate-100">
                    <td className="px-3 py-3 font-medium">
                      {r.customerName}
                      {r.scenarioTag ? (
                        <span className="ml-2 badge bg-violet-50 text-violet-700">
                          Demo case {r.scenarioTag}
                        </span>
                      ) : null}
                    </td>
                    <td className="px-3 py-3">{friendlyStatus(r.segment)}</td>
                    <td className="px-3 py-3">{r.city}</td>
                    <td className="px-3 py-3">
                      ₹{Number(r.monthlyIncome).toLocaleString("en-IN")}
                    </td>
                    <td className="px-3 py-3">{r.valueScore?.toFixed?.(1) ?? r.valueScore}</td>
                    <td className="px-3 py-3">
                      {r.propensityScore?.toFixed?.(1) ?? r.propensityScore}
                    </td>
                    <td className="px-3 py-3">{r.recommendedProduct || "—"}</td>
                    <td className="px-3 py-3">{friendlyStatus(r.eligibility)}</td>
                    <td className="px-3 py-3">
                      <span
                        className={`badge ${
                          r.contactAllowed
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-red-50 text-red-700"
                        }`}
                      >
                        {r.contactAllowed ? "Yes — cleared" : "No — blocked"}
                      </span>
                    </td>
                    <td className="px-3 py-3">{friendlyStatus(r.messageStatus || "NONE")}</td>
                    <td className="px-3 py-3">
                      <Link
                        className={`btn-sm ${r.contactAllowed ? "btn-primary" : "btn-secondary"}`}
                        to={`/campaigns/${campaignId}/customers/${r.customerId}`}
                      >
                        {actionLabelForResult(r)}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
