import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, Send, X } from "lucide-react";
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";
import { PageLoader } from "../components/PageLoader";
import { RmJourneyWizard } from "../components/RmJourneyWizard";
import { friendlyStatus } from "../lib/labels";
import { useToast } from "../components/toast/ToastProvider";
import { useQueryErrorToast } from "../hooks/useQueryToasts";

export function CustomerDetailPage() {
  const { campaignId, customerId } = useParams();
  const qc = useQueryClient();
  const toast = useToast();
  const [body, setBody] = useState("");
  const [notice, setNotice] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["customer", campaignId, customerId],
    queryFn: () =>
      api<{
        profile: any;
        campaignContext: any;
      }>(`/customers/${customerId}?campaign_id=${campaignId}`),
  });

  useQueryErrorToast(error, "Could not load customer details");

  useEffect(() => {
    const msg = data?.campaignContext?.message?.body;
    if (msg) setBody(msg);
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: () =>
      api(`/messages/${data?.campaignContext?.message?.id}`, {
        method: "PATCH",
        body: JSON.stringify({ body }),
      }),
    onSuccess: () => {
      setNotice("Draft saved. You can approve it when ready.");
      toast.success("Draft saved", "Message updated");
      qc.invalidateQueries({ queryKey: ["customer", campaignId, customerId] });
    },
    onError: (e: Error) => {
      setNotice(e.message);
      toast.error(e.message, "Save failed");
    },
  });

  const approveMutation = useMutation({
    mutationFn: () =>
      api(`/messages/${data?.campaignContext?.message?.id}/approve`, { method: "POST" }),
    onSuccess: () => {
      setNotice("Approved. You can now send a mock WhatsApp.");
      toast.success("Message approved. You can send a mock WhatsApp now.", "Approved");
      qc.invalidateQueries({ queryKey: ["customer", campaignId, customerId] });
    },
    onError: (e: Error) => {
      setNotice(e.message);
      toast.error(e.message, "Approve failed");
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () =>
      api(`/messages/${data?.campaignContext?.message?.id}/reject`, { method: "POST" }),
    onSuccess: () => {
      setNotice("Rejected. This message will not be sent.");
      toast.info("Message rejected. It will not be sent.", "Rejected");
      qc.invalidateQueries({ queryKey: ["customer", campaignId, customerId] });
    },
    onError: (e: Error) => {
      setNotice(e.message);
      toast.error(e.message, "Reject failed");
    },
  });

  const sendMutation = useMutation({
    mutationFn: () =>
      api<{ disclaimer: string }>(
        `/messages/${data?.campaignContext?.message?.id}/simulate-send`,
        { method: "POST" },
      ),
    onSuccess: (res) => {
      setNotice(res.disclaimer);
      toast.success(res.disclaimer || "Mock WhatsApp send completed.", "Sent (mock)");
      qc.invalidateQueries({ queryKey: ["customer", campaignId, customerId] });
    },
    onError: (e: Error) => {
      setNotice(e.message);
      toast.error(e.message, "Send failed");
    },
  });

  if (isLoading) return <PageLoader label="Loading customer review..." />;
  if (error) return <p className="text-red-600">{(error as Error).message}</p>;
  if (!data) return null;

  const profile = data.profile;
  const ctx = data.campaignContext || {};
  const valueComponents = Object.entries(ctx.valueScore?.componentScores || {}).map(
    ([name, score]) => ({ name, score }),
  );
  const contactAllowed = Boolean(ctx.compliance?.contactAllowed);
  const messageStatus = ctx.message?.status;
  const canApprove = Boolean(ctx.message) && contactAllowed && messageStatus !== "SIMULATED_SENT";
  const canSend = messageStatus === "APPROVED" && contactAllowed;

  return (
    <div className="space-y-5">
      <RmJourneyWizard current="customer" campaignId={campaignId} />
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Review · {profile.fullName}</h1>
          <p className="text-sm text-amber-700">
            Demonstration only. Scores and offers are not real lending decisions.
          </p>
          <p className="text-sm text-slate-500 mt-1">
            Check scores, edit the draft if needed, then approve and mock-send.
          </p>
        </div>
        <Link to={`/campaigns/${campaignId}/results`} className="btn-secondary">
          <ArrowLeft size={16} /> Back to shortlist
        </Link>
      </div>

      {(notice || messageStatus === "SIMULATED_SENT") && (
        <div className="rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-900">
          {notice || "Mock WhatsApp send completed. No real customer was contacted."}
        </div>
      )}

      <section className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4 space-y-2">
          <h2 className="font-semibold">Customer profile</h2>
          <Info label="Age" value={profile.age} />
          <Info label="City" value={profile.city} />
          <Info label="Occupation" value={profile.occupation} />
          <Info label="Segment" value={friendlyStatus(profile.customerSegment)} />
          <Info
            label="Monthly income"
            value={`₹${Number(profile.monthlyIncome).toLocaleString("en-IN")}`}
          />
          <Info label="Tenure (years)" value={profile.tenureYears} />
          <Info label="Products" value={(profile.existingProducts || []).join(", ")} />
        </div>
        <div className="card p-4 space-y-2">
          <h2 className="font-semibold">Account summary</h2>
          {(profile.accounts || []).map((a: any) => (
            <div key={a.accountId} className="rounded-lg border border-slate-100 p-3 text-sm">
              <p className="font-medium">
                {a.accountType} · {a.maskedAccountNumber}
              </p>
              <p className="text-slate-500">
                Avg bal ₹{Number(a.averageMonthlyBalance).toLocaleString("en-IN")} ·{" "}
                {friendlyStatus(a.status)}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4">
          <h2 className="font-semibold">Customer value score</h2>
          <p className="text-3xl font-bold mt-2">{ctx.valueScore?.overallScore ?? "—"}</p>
          <p className="text-sm text-slate-500">
            {friendlyStatus(ctx.valueScore?.classification)}
          </p>
          <div className="h-48 mt-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={valueComponents}>
                <XAxis dataKey="name" hide />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="score" fill="#0284c7" radius={4} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-sm mt-2 text-slate-600">{ctx.valueScore?.explanation}</p>
        </div>
        <div className="card p-4 space-y-2">
          <h2 className="font-semibold">Conversion chance</h2>
          <p className="text-3xl font-bold">{ctx.propensityScore?.overallScore ?? "—"}</p>
          <p className="text-sm text-slate-500">
            {friendlyStatus(ctx.propensityScore?.classification)}
          </p>
          <p className="text-sm text-slate-600">{ctx.propensityScore?.explanation}</p>
          <p className="text-xs text-amber-700 font-medium">
            Demo score only — not a credit or underwriting model.
          </p>
        </div>
      </section>

      <section className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4 space-y-2">
          <h2 className="font-semibold">Suggested product</h2>
          <Info label="Product" value={ctx.recommendation?.productName || "—"} />
          <Info label="Why this product" value={ctx.recommendation?.reason || "—"} />
          <Info
            label="Indicative amount"
            value={
              ctx.recommendation
                ? `₹${Number(ctx.recommendation.indicativeAmountMin).toLocaleString("en-IN")} - ₹${Number(ctx.recommendation.indicativeAmountMax).toLocaleString("en-IN")}`
                : "—"
            }
          />
          <Info
            label="Indicative rate"
            value={ctx.recommendation ? `${ctx.recommendation.indicativeRate}%` : "—"}
          />
          <p className="text-xs text-amber-700">Demo data only. Not a real bank offer.</p>
        </div>
        <div className="card p-4 space-y-2">
          <h2 className="font-semibold">Eligibility checks</h2>
          {(ctx.eligibility?.rules || []).map((r: any) => (
            <div
              key={r.ruleCode}
              className="flex items-center justify-between text-sm border-b border-slate-100 py-1"
            >
              <span>{r.ruleName}</span>
              <span
                className={`badge ${r.passed ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}
              >
                {r.passed ? "Passed" : "Failed"}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="card p-4 space-y-2">
        <h2 className="font-semibold">Compliance & consent</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
          <Info
            label="Marketing consent"
            value={ctx.compliance?.details?.marketingConsent ? "Yes" : "No"}
          />
          <Info
            label="WhatsApp consent"
            value={ctx.compliance?.details?.whatsappConsent ? "Yes" : "No"}
          />
          <Info
            label="Do not contact"
            value={ctx.compliance?.details?.doNotContact ? "Yes" : "No"}
          />
          <Info
            label="Contacts this month"
            value={`${ctx.compliance?.details?.contactsThisMonth}/${ctx.compliance?.details?.maximumContactsPerMonth}`}
          />
        </div>
        <p className="text-sm">{ctx.compliance?.explanation}</p>
        {!contactAllowed && (
          <p className="text-sm font-semibold text-red-700">
            Contact blocked. Approve and send stay disabled for this customer.
          </p>
        )}
      </section>

      <section className="card p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-semibold">WhatsApp message draft</h2>
          <span className="badge bg-slate-100 text-slate-700">
            {friendlyStatus(messageStatus || "NONE")}
          </span>
        </div>
        {ctx.message ? (
          <>
            <textarea
              className="field min-h-32"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              disabled={!contactAllowed || messageStatus === "SIMULATED_SENT"}
            />
            <div className="flex flex-wrap gap-2">
              <button
                className="btn-secondary"
                onClick={() => saveMutation.mutate()}
                disabled={!canApprove || saveMutation.isPending}
              >
                Save draft
              </button>
              <button
                className="btn-success"
                onClick={() => approveMutation.mutate()}
                disabled={!canApprove || approveMutation.isPending}
              >
                <Check size={16} /> Approve message
              </button>
              <button
                className="btn-danger"
                onClick={() => rejectMutation.mutate()}
                disabled={!canApprove || rejectMutation.isPending}
              >
                <X size={16} /> Reject
              </button>
              <button
                className="btn-primary"
                onClick={() => sendMutation.mutate()}
                disabled={!canSend || sendMutation.isPending}
              >
                <Send size={16} /> Send mock WhatsApp
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Flow: Save (optional) → Approve → Send mock WhatsApp. No real message leaves this demo.
            </p>
          </>
        ) : (
          <p className="text-sm text-slate-500">
            No message was drafted (customer ineligible or compliance blocked).
          </p>
        )}
      </section>
    </div>
  );
}

function Info({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="text-sm">
      <p className="text-slate-500">{label}</p>
      <p className="font-medium text-slate-800">{value}</p>
    </div>
  );
}
