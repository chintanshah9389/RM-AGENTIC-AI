import { Link } from "react-router-dom";
import { ArrowRight, Check } from "lucide-react";

export type JourneyStepId =
  | "dashboard"
  | "create"
  | "workflow"
  | "results"
  | "customer";

const STEPS: {
  id: JourneyStepId;
  number: number;
  title: string;
  help: string;
  to?: string;
}[] = [
  {
    id: "dashboard",
    number: 1,
    title: "Home",
    help: "See your numbers, then start a new outreach campaign",
    to: "/",
  },
  {
    id: "create",
    number: 2,
    title: "New campaign",
    help: "Describe who to find and click Start AI campaign",
    to: "/campaigns/new",
  },
  {
    id: "workflow",
    number: 3,
    title: "AI working",
    help: "Agents find, score, and draft messages for you",
  },
  {
    id: "results",
    number: 4,
    title: "Pick customer",
    help: "Choose a cleared customer to review the message",
  },
  {
    id: "customer",
    number: 5,
    title: "Approve & send",
    help: "Edit if needed, approve, then send a mock WhatsApp",
  },
];

type Props = {
  current: JourneyStepId;
  campaignId?: string;
  workflowId?: string;
  /** When false on the AI-working step, block jumping ahead to results. */
  allowNext?: boolean;
};

export function RmJourneyWizard({
  current,
  campaignId,
  workflowId,
  allowNext = true,
}: Props) {
  const currentIndex = STEPS.findIndex((s) => s.id === current);
  const nextStep = STEPS[currentIndex + 1];
  const progressPct =
    STEPS.length <= 1 ? 0 : Math.round((currentIndex / (STEPS.length - 1)) * 100);

  function hrefFor(step: (typeof STEPS)[number]) {
    if (step.id === "workflow" && campaignId && workflowId) {
      return `/campaigns/${campaignId}/workflow/${workflowId}`;
    }
    if (step.id === "results" && campaignId) {
      return `/campaigns/${campaignId}/results`;
    }
    return step.to;
  }

  const canAdvanceToNext =
    allowNext || !(current === "workflow" && nextStep?.id === "results");

  const nextHref =
    canAdvanceToNext &&
    nextStep &&
    (hrefFor(nextStep) ||
      (nextStep.id === "results" && campaignId
        ? `/campaigns/${campaignId}/results`
        : nextStep.to));

  return (
    <div className="card mb-5 overflow-hidden border-sky-100">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-gradient-to-r from-white to-sky-50/70 px-4 py-3 sm:px-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-sky-700">
            Campaign wizard
          </p>
          <p className="text-sm text-slate-600">
            Step {currentIndex + 1} of {STEPS.length}
            <span className="mx-1.5 text-slate-300">·</span>
            <span className="font-medium text-slate-800">{STEPS[currentIndex]?.title}</span>
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-xs text-amber-700 font-medium">Demo · Fake customer data</p>
          {nextHref && (
            <Link to={nextHref} className="btn-primary btn-sm">
              Next step <ArrowRight size={14} />
            </Link>
          )}
        </div>
      </div>

      <div className="px-4 py-5 sm:px-6 sm:py-6">
        {/* Horizontal stepper */}
        <div className="relative mx-auto max-w-5xl">
          {/* Progress track between step circles */}
          <div
            className="pointer-events-none absolute left-[10%] right-[10%] top-4 hidden h-0.5 md:block"
            aria-hidden
          >
            <div className="h-full w-full rounded-full bg-slate-200" />
            <div
              className="absolute inset-y-0 left-0 rounded-full bg-sky-500 transition-all duration-500"
              style={{ width: `${progressPct}%` }}
            />
          </div>

          <ol className="relative grid grid-cols-1 gap-4 md:grid-cols-5 md:gap-2">
            {STEPS.map((step, idx) => {
              const done = idx < currentIndex;
              const active = idx === currentIndex;
              const href = hrefFor(step);
              const isFutureResults =
                current === "workflow" && step.id === "results" && !allowNext;
              const clickable = Boolean(
                href &&
                  !isFutureResults &&
                  (done || active || (idx === currentIndex + 1 && canAdvanceToNext)),
              );

              const circle = (
                <span
                  className={`relative z-10 inline-flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-bold transition ${
                    active
                      ? "border-sky-600 bg-sky-600 text-white ring-4 ring-sky-100"
                      : done
                        ? "border-emerald-600 bg-emerald-600 text-white"
                        : "border-slate-300 bg-white text-slate-500"
                  }`}
                >
                  {done ? <Check size={16} strokeWidth={3} /> : step.number}
                </span>
              );

              const label = (
                <div className="md:mt-3 md:text-center">
                  <p
                    className={`text-sm font-semibold ${
                      active ? "text-sky-800" : done ? "text-emerald-800" : "text-slate-600"
                    }`}
                  >
                    {step.title}
                  </p>
                  {active && (
                    <p className="mt-0.5 text-[11px] font-semibold uppercase tracking-wide text-sky-600">
                      Current
                    </p>
                  )}
                  {done && !active && (
                    <p className="mt-0.5 text-[11px] font-medium text-emerald-600">Done</p>
                  )}
                </div>
              );

              const rowClass =
                "flex items-center gap-3 md:flex-col md:items-center md:justify-start";

              if (clickable && href) {
                return (
                  <li key={step.id}>
                    <Link
                      to={href}
                      className={`${rowClass} rounded-lg p-1 hover:bg-sky-50/80 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-300`}
                      aria-current={active ? "step" : undefined}
                    >
                      {circle}
                      {label}
                    </Link>
                  </li>
                );
              }

              return (
                <li key={step.id} className={rowClass} aria-current={active ? "step" : undefined}>
                  {circle}
                  {label}
                </li>
              );
            })}
          </ol>
        </div>

        {/* Current instruction */}
        <div className="mt-5 rounded-lg border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-950">
          <span className="font-semibold">What to do now: </span>
          {STEPS[currentIndex]?.help}
        </div>
      </div>
    </div>
  );
}
