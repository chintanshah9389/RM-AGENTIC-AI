import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Sparkles } from "lucide-react";
import { api } from "../api/client";
import { BehindScenesSetupModal } from "../components/BehindScenesSetupModal";
import { InlineLoader } from "../components/PageLoader";
import { RmJourneyWizard } from "../components/RmJourneyWizard";
import { useToast } from "../components/toast/ToastProvider";

const DEFAULT_REQUEST =
  "Find high-value customers likely to convert for a Personal Loan this month and prepare personalized WhatsApp messages.";

/** Example prompts only — product/channel are decided by Intent agent + catalogue tools. */
const chips = [
  {
    label: "Personal Loan example",
    text: "Find Premium customers for Personal Loan WhatsApp outreach",
  },
  {
    label: "Home Loan example",
    text: "Find high-value customers for a Home Loan this month and prepare personalized WhatsApp messages",
  },
  {
    label: "Credit Card example",
    text: "Find eligible customers for a Credit Card offer on WhatsApp",
  },
  {
    label: "Unavailable product example",
    text: "Find customers interested in a Gold Loan this month and prepare WhatsApp messages",
  },
];

export function CreateCampaignPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const [name, setName] = useState("RM outreach campaign");
  const [request, setRequest] = useState(DEFAULT_REQUEST);
  const [maxCustomers, setMaxCustomers] = useState(10);
  const [minValue, setMinValue] = useState(70);
  const [minPropensity, setMinPropensity] = useState(60);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [bootstrapping, setBootstrapping] = useState(false);
  const [campaignId, setCampaignId] = useState<string | null>(null);
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [modalError, setModalError] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setModalError("");
    setCampaignId(null);
    setWorkflowId(null);
    setModalOpen(true);
    setBootstrapping(true);
    try {
      const campaign = await api<{ id: string }>("/campaigns", {
        method: "POST",
        body: JSON.stringify({
          name,
          natural_language_request: request,
          product_category: "AUTO",
          channel: "AUTO",
          max_customers: maxCustomers,
          min_value_score: minValue,
          min_propensity_score: minPropensity,
        }),
      });
      setCampaignId(campaign.id);
      toast.success("Campaign created. Opening behind-the-scenes setup…", "Campaign ready");

      const run = await api<{ workflow: { id: string } }>(`/campaigns/${campaign.id}/run`, {
        method: "POST",
      });
      setWorkflowId(run.workflow.id);
      toast.success("Agents started — watch the live setup log", "AI running");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to start campaign";
      setError(message);
      setModalError(message);
      toast.error(message, "Campaign failed");
    } finally {
      setBootstrapping(false);
      setLoading(false);
    }
  }

  function goToPreview(opts: { ready: boolean; failed: boolean }) {
    if (!campaignId || !workflowId) return;
    setModalOpen(false);
    if (opts.ready) {
      navigate(`/campaigns/${campaignId}/results`);
      return;
    }
    navigate(`/campaigns/${campaignId}/workflow/${workflowId}`);
  }

  return (
    <div className="w-full space-y-4">
      <RmJourneyWizard current="create" />
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold">Create outreach campaign</h1>
          <p className="text-sm text-slate-500 mt-1">
            Describe the goal in plain English. AI agents choose product and channel from your
            request and the live product catalogue — nothing is hardcoded on this form.
          </p>
        </div>
        <Link to="/customers" className="btn-secondary btn-sm">
          Browse customers first
        </Link>
      </div>

      <form onSubmit={onSubmit} className="card p-6 lg:p-8 w-full space-y-6">
        <div className="grid lg:grid-cols-2 gap-6 lg:gap-8">
          <div className="space-y-5">
            <label className="block text-sm">
              <span className="font-medium">Campaign name</span>
              <input
                className="field"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="e.g. March outreach push"
              />
            </label>

            <label className="block text-sm">
              <span className="font-medium">What should the AI do?</span>
              <textarea
                className="field min-h-40"
                value={request}
                onChange={(e) => setRequest(e.target.value)}
                required
              />
              <span className="mt-1 block text-xs text-slate-500">
                Mention the product you want (must exist in the catalogue), channel, and who to
                target. Agents resolve the rest.
              </span>
            </label>

            <div>
              <p className="text-sm font-medium mb-2">Example requests (optional)</p>
              <div className="flex flex-wrap gap-2">
                {chips.map((c) => (
                  <button
                    type="button"
                    key={c.label}
                    className="btn-secondary btn-sm"
                    onClick={() => setRequest(c.text)}
                  >
                    {c.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-5">
            <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4 space-y-4">
              <p className="text-sm font-semibold text-slate-800">Optional score filters</p>
              <div className="grid sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3 gap-3">
                <label className="text-sm">
                  <span className="font-medium">How many customers?</span>
                  <input
                    type="number"
                    className="field"
                    value={maxCustomers}
                    min={1}
                    max={50}
                    onChange={(e) => setMaxCustomers(Number(e.target.value))}
                  />
                </label>
                <label className="text-sm">
                  <span className="font-medium">Min. value score</span>
                  <input
                    type="number"
                    className="field"
                    value={minValue}
                    min={0}
                    max={100}
                    onChange={(e) => setMinValue(Number(e.target.value))}
                  />
                </label>
                <label className="text-sm">
                  <span className="font-medium">Min. conversion score</span>
                  <input
                    type="number"
                    className="field"
                    value={minPropensity}
                    min={0}
                    max={100}
                    onChange={(e) => setMinPropensity(Number(e.target.value))}
                  />
                </label>
              </div>
            </div>

            <div className="rounded-xl border border-sky-100 bg-sky-50/70 p-4 text-sm text-sky-950 space-y-2">
              <p className="font-semibold">What happens next</p>
              <ol className="list-decimal list-inside space-y-1 text-sky-900/90">
                <li>A popup shows live behind-the-scenes agent / tool / LLM activity</li>
                <li>When ready, continue to the workflow preview and shortlist</li>
                <li>You approve drafts, then mock-send</li>
              </ol>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <div className="flex flex-wrap gap-2 pt-1">
              <button disabled={loading} className="btn-primary">
                {loading ? (
                  <InlineLoader label="Starting AI agents..." />
                ) : (
                  <>
                    <Sparkles size={16} />
                    Start AI campaign
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
              <Link to="/" className="btn-secondary">
                Cancel
              </Link>
            </div>
          </div>
        </div>
      </form>

      <BehindScenesSetupModal
        open={modalOpen}
        campaignId={campaignId}
        workflowId={workflowId}
        bootstrapping={bootstrapping}
        error={modalError}
        onClose={() => setModalOpen(false)}
        onContinueToPreview={goToPreview}
      />
    </div>
  );
}
