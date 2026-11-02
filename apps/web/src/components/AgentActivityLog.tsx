import { useEffect, useMemo, useRef } from "react";
import { Bot, Cpu, Loader2, Terminal, Wrench } from "lucide-react";
import { friendlyAgent } from "../lib/labels";

export type ActivityLine = { kind: string; text: string };

export type WorkflowStepActivity = {
  id: string;
  agentName: string;
  status: string;
  summary?: string;
  startedAt?: string | null;
  completedAt?: string | null;
  activity?: ActivityLine[];
};

export type AuditActivityEvent = {
  id: string;
  timestamp: string;
  agentName?: string | null;
  eventType: string;
  status: string;
  summary: string;
};

function kindTone(kind: string) {
  if (kind === "tool") return "text-amber-300";
  if (kind === "llm") return "text-sky-300";
  if (kind === "warn") return "text-rose-300";
  if (kind === "intent") return "text-violet-300";
  if (kind === "data") return "text-emerald-300";
  if (kind === "human") return "text-amber-200";
  if (kind === "orch") return "text-cyan-300";
  if (kind === "timing") return "text-slate-400";
  return "text-slate-200";
}

function kindIcon(kind: string) {
  if (kind === "tool") return <Wrench size={12} className="shrink-0 mt-0.5" />;
  if (kind === "llm") return <Cpu size={12} className="shrink-0 mt-0.5" />;
  if (kind === "agent" || kind === "orch") return <Bot size={12} className="shrink-0 mt-0.5" />;
  return <Terminal size={12} className="shrink-0 mt-0.5" />;
}

export function buildActivityTimeline(
  steps: WorkflowStepActivity[] | undefined,
  auditEvents: AuditActivityEvent[] | undefined,
) {
  const rows: {
    id: string;
    time?: string;
    agent?: string;
    kind: string;
    text: string;
  }[] = [];

  for (const ev of auditEvents || []) {
    if (ev.eventType === "AGENT_COMPLETED") continue;
    rows.push({
      id: `audit-${ev.id}`,
      time: ev.timestamp,
      agent: ev.agentName || undefined,
      kind: ev.status === "FAILED" ? "warn" : "orch",
      text: `[${ev.eventType}] ${ev.summary}`,
    });
  }

  for (const step of steps || []) {
    if (step.status === "PENDING") continue;
    const stamp = step.completedAt || step.startedAt || undefined;
    const activity = step.activity || [];
    if (activity.length === 0 && step.summary) {
      rows.push({
        id: `${step.id}-summary`,
        time: stamp,
        agent: step.agentName,
        kind: "summary",
        text: step.summary,
      });
      continue;
    }
    for (const [idx, line] of activity.entries()) {
      rows.push({
        id: `${step.id}-${idx}`,
        time: stamp,
        agent: step.agentName,
        kind: line.kind,
        text: line.text,
      });
    }
  }

  return rows;
}

type AgentActivityLogProps = {
  steps?: WorkflowStepActivity[];
  auditEvents?: AuditActivityEvent[];
  isRunning?: boolean;
  maxHeightClass?: string;
  emptyLabel?: string;
};

export function AgentActivityLog({
  steps,
  auditEvents,
  isRunning = false,
  maxHeightClass = "max-h-80",
  emptyLabel = "Waiting for the first agent to start…",
}: AgentActivityLogProps) {
  const logRef = useRef<HTMLDivElement>(null);
  const timeline = useMemo(
    () => buildActivityTimeline(steps, auditEvents),
    [steps, auditEvents],
  );

  useEffect(() => {
    const el = logRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [timeline.length, isRunning]);

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-950 text-slate-100 shadow-md">
      <div className="flex items-center gap-2 border-b border-slate-800 px-4 py-2.5 text-xs text-slate-400">
        <Terminal size={14} />
        <span>Live agent / tool / LLM activity</span>
        <span className="ml-auto text-slate-500">{timeline.length} lines</span>
        {isRunning ? (
          <span className="inline-flex items-center gap-1 text-sky-400">
            <Loader2 size={12} className="animate-spin" /> streaming
          </span>
        ) : (
          <span className="text-emerald-400">idle</span>
        )}
      </div>
      <div
        ref={logRef}
        className={`${maxHeightClass} overflow-auto px-3 py-3 font-mono text-[11px] leading-relaxed space-y-1.5`}
      >
        {timeline.length === 0 ? (
          <p className="text-slate-500 px-1">{emptyLabel}</p>
        ) : (
          timeline.map((row) => (
            <div key={row.id} className={`flex gap-2 ${kindTone(row.kind)}`}>
              {kindIcon(row.kind)}
              <div className="min-w-0 break-words">
                <span className="text-slate-500">
                  {row.time
                    ? new Date(row.time).toLocaleTimeString("en-IN", {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })
                    : "--:--:--"}
                </span>
                {row.agent ? (
                  <span className="text-slate-400"> · {friendlyAgent(row.agent)}</span>
                ) : null}
                <span className="text-slate-600"> · </span>
                <span>{row.text}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
