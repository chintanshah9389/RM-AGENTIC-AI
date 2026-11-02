"""Build RM-friendly behind-the-scenes activity lines from workflow step details."""

from __future__ import annotations

from typing import Any


INTENT_KEYS = (
    "productCategory",
    "requestedProductCategory",
    "productCategoryResolved",
    "productCategorySource",
    "channel",
    "customerSegment",
    "provider",
    "executionMode",
    "toolsUsed",
    "agentFramework",
    "productUnavailableMessage",
    "availableProductCategories",
    "maximumCustomers",
)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def sanitize_step_details(details: dict[str, Any] | None) -> dict[str, Any]:
    """Keep telemetry useful for the UI; drop large customer/score payloads."""
    if not details:
        return {}

    out: dict[str, Any] = {}
    for key, value in details.items():
        if key in {
            "candidateCustomers",
            "customerValueResults",
            "propensityResults",
            "productRecommendations",
            "eligibilityResults",
            "complianceResults",
            "messageDrafts",
            "explanations",
            "rankedCustomers",
        }:
            out[f"{key}Count"] = len(value) if isinstance(value, list) else 0
            continue
        if key == "parsedIntent" and isinstance(value, dict):
            out["parsedIntent"] = {k: value[k] for k in INTENT_KEYS if k in value}
            continue
        if key == "retrievalPlan" and isinstance(value, dict):
            out["retrievalPlan"] = {
                k: value[k]
                for k in (
                    "segmentHint",
                    "minIncome",
                    "limit",
                    "notes",
                    "toolsUsed",
                    "executionMode",
                    "agentFramework",
                )
                if k in value
            }
            continue
        if key in {
            "executionMode",
            "toolsUsed",
            "toolsCalled",
            "provider",
            "agentFramework",
            "processedRecords",
            "orchestratorEngine",
            "pipeline",
            "noDataReason",
        }:
            out[key] = value
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            if key not in {"completedSteps", "errors", "workflowStatus", "currentStep"}:
                out[key] = value
    return out


def build_activity_lines(
    *,
    agent_name: str,
    status: str,
    summary: str | None,
    details: dict[str, Any] | None,
    processed_records: int = 0,
    duration_ms: int | None = None,
) -> list[dict[str, str]]:
    """Human-readable log lines for one workflow step."""
    lines: list[dict[str, str]] = []
    d = details or {}
    intent = d.get("parsedIntent") if isinstance(d.get("parsedIntent"), dict) else {}
    plan = d.get("retrievalPlan") if isinstance(d.get("retrievalPlan"), dict) else {}

    if status == "PENDING":
        lines.append({"kind": "wait", "text": f"{agent_name} queued"})
        return lines

    if status == "RUNNING":
        lines.append({"kind": "agent", "text": f"{agent_name} started"})
        return lines

    lines.append({"kind": "agent", "text": f"{agent_name} selected"})

    framework = (
        intent.get("agentFramework")
        or plan.get("agentFramework")
        or d.get("agentFramework")
    )
    if framework:
        lines.append({"kind": "llm", "text": f"Agent framework: {framework}"})

    mode = intent.get("executionMode") or plan.get("executionMode") or d.get("executionMode")
    if mode:
        lines.append({"kind": "llm", "text": f"LLM / runtime mode: {mode}"})

    provider = intent.get("provider") or d.get("provider")
    if provider:
        lines.append({"kind": "llm", "text": f"LLM provider: {provider}"})

    engine = d.get("orchestratorEngine")
    if engine:
        lines.append({"kind": "orch", "text": f"Orchestrator engine: {engine}"})

    pipeline = d.get("pipeline")
    if isinstance(pipeline, list) and pipeline:
        lines.append(
            {
                "kind": "orch",
                "text": f"Pipeline agents: {', '.join(str(p) for p in pipeline)}",
            }
        )

    tools = (
        _as_list(intent.get("toolsUsed"))
        or _as_list(plan.get("toolsUsed"))
        or _as_list(d.get("toolsUsed"))
        or _as_list(d.get("toolsCalled"))
    )
    if tools:
        for tool in tools:
            lines.append({"kind": "tool", "text": f"Called tool: {tool}"})
    elif any(
        name in agent_name
        for name in (
            "Intent",
            "Retrieval",
            "Message",
        )
    ):
        lines.append({"kind": "tool", "text": "No catalogue/DB tools invoked for this step"})

    if intent:
        requested = intent.get("requestedProductCategory") or intent.get("productCategory")
        if requested:
            resolved = intent.get("productCategoryResolved")
            lines.append(
                {
                    "kind": "intent",
                    "text": (
                        f"Product intent: {requested}"
                        + (
                            " (matched catalogue)"
                            if resolved
                            else " (not in catalogue — shortlist will be empty)"
                        )
                    ),
                }
            )
        if intent.get("channel"):
            lines.append({"kind": "intent", "text": f"Channel: {intent.get('channel')}"})
        if intent.get("customerSegment"):
            lines.append(
                {"kind": "intent", "text": f"Segment focus: {intent.get('customerSegment')}"}
            )
        if intent.get("productUnavailableMessage"):
            lines.append(
                {"kind": "warn", "text": str(intent.get("productUnavailableMessage"))}
            )

    if plan:
        lines.append(
            {
                "kind": "tool",
                "text": (
                    f"Retrieval plan: segment={plan.get('segmentHint')}, "
                    f"minIncome={plan.get('minIncome')}, limit={plan.get('limit')}"
                ),
            }
        )

    for list_key, label in (
        ("candidateCustomersCount", "customers retrieved"),
        ("customerValueResultsCount", "value scores"),
        ("propensityResultsCount", "propensity scores"),
        ("productRecommendationsCount", "product recommendations"),
        ("eligibilityResultsCount", "eligibility checks"),
        ("complianceResultsCount", "compliance checks"),
        ("messageDraftsCount", "message drafts"),
        ("explanationsCount", "explanations"),
    ):
        count = d.get(list_key)
        if isinstance(count, int) and count > 0:
            lines.append({"kind": "data", "text": f"Produced {count} {label}"})

    if processed_records:
        lines.append({"kind": "data", "text": f"Processed records: {processed_records}"})

    if summary:
        lines.append({"kind": "summary", "text": summary})

    if duration_ms is not None:
        lines.append({"kind": "timing", "text": f"Completed in {duration_ms} ms"})

    if status == "WAITING_FOR_APPROVAL":
        lines.append({"kind": "human", "text": "Handed off to RM for approval"})

    if d.get("noDataReason"):
        lines.append({"kind": "warn", "text": str(d.get("noDataReason"))})

    return lines


def extract_agent_telemetry(update: dict[str, Any]) -> dict[str, Any]:
    """Compact telemetry for audit metadata from an agent update dict."""
    intent = update.get("parsedIntent") if isinstance(update.get("parsedIntent"), dict) else {}
    plan = update.get("retrievalPlan") if isinstance(update.get("retrievalPlan"), dict) else {}
    tools = (
        intent.get("toolsUsed")
        or plan.get("toolsUsed")
        or update.get("toolsUsed")
        or update.get("toolsCalled")
        or []
    )
    return {
        "executionMode": intent.get("executionMode")
        or plan.get("executionMode")
        or update.get("executionMode"),
        "provider": intent.get("provider") or update.get("provider"),
        "agentFramework": intent.get("agentFramework")
        or plan.get("agentFramework")
        or update.get("agentFramework"),
        "toolsUsed": tools,
        "processedRecords": update.get("processedRecords"),
        "productCategory": intent.get("productCategory"),
        "requestedProductCategory": intent.get("requestedProductCategory"),
        "productCategoryResolved": intent.get("productCategoryResolved"),
    }
