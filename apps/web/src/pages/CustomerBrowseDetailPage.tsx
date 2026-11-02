import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { api } from "../api/client";
import { PageLoader } from "../components/PageLoader";
import { RmJourneyWizard } from "../components/RmJourneyWizard";
import { friendlyStatus } from "../lib/labels";
import { useQueryErrorToast } from "../hooks/useQueryToasts";

export function CustomerBrowseDetailPage() {
  const { customerId } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["customer-browse", customerId],
    queryFn: () => api<{ profile: any }>(`/customers/${customerId}`),
  });

  useQueryErrorToast(error, "Customer not found or could not be loaded");

  if (isLoading) return <PageLoader label="Loading customer profile..." />;
  if (error) return <p className="text-red-600">{(error as Error).message}</p>;
  if (!data) return null;
  const p = data.profile;

  return (
    <div className="space-y-4">
      <RmJourneyWizard current="dashboard" />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">{p.fullName}</h1>
          <p className="text-sm text-slate-500">
            {p.customerCode} · {friendlyStatus(p.customerSegment)} · {p.city}
          </p>
          <p className="text-sm text-amber-700 mt-1">
            Demonstration only. Synthetic customer profile.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/customers" className="btn-secondary">
            <ArrowLeft size={16} /> Back to list
          </Link>
          <Link to="/campaigns/new" className="btn-primary">
            Score via AI campaign <ArrowRight size={16} />
          </Link>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <div className="card p-4 space-y-3 text-sm">
          <h2 className="font-semibold text-base">Profile</h2>
          <Info label="Age" value={p.age} />
          <Info label="Occupation" value={p.occupation} />
          <Info
            label="Monthly income"
            value={`₹${Number(p.monthlyIncome).toLocaleString("en-IN")}`}
          />
          <Info label="Relationship tenure" value={`${p.tenureYears} years`} />
          <Info label="Products held" value={(p.existingProducts || []).join(", ")} />
          <Info label="Digital engagement" value={p.digitalEngagementScore} />
        </div>
        <div className="card p-4 space-y-3 text-sm">
          <h2 className="font-semibold text-base">Accounts (masked)</h2>
          {(p.accounts || []).map((a: any) => (
            <div key={a.accountId} className="border border-slate-100 rounded-lg p-3">
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
      </div>

      <div className="card p-4 text-sm space-y-3">
        <h2 className="font-semibold text-base">Consent snapshot</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          <Info
            label="Marketing consent"
            value={p.consent?.marketingConsent ? "Yes" : "No"}
          />
          <Info
            label="WhatsApp consent"
            value={p.consent?.whatsappConsent ? "Yes" : "No"}
          />
          <Info
            label="Do not contact"
            value={p.consent?.doNotContact ? "Yes" : "No"}
          />
          <Info
            label="Contacts this month"
            value={`${p.consent?.contactsThisMonth}/${p.consent?.maximumContactsPerMonth}`}
          />
        </div>
      </div>

      <div className="rounded-xl border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900">
        This page is for browsing only. To get AI scores and a WhatsApp draft, start a campaign.
        <div className="mt-3">
          <Link to="/campaigns/new" className="btn-primary">
            Start AI campaign
          </Link>
        </div>
      </div>
    </div>
  );
}

function Info({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <p className="text-slate-500">{label}</p>
      <p className="font-medium text-slate-800">{value}</p>
    </div>
  );
}
