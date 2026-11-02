from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.lc_runner import run_create_agent
from app.agents.schemas import MessageDraftSchema
from app.agents.validation import validate_message_body
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.tools.langchain_tools import build_crm_tools, invoke_tool


class MessageGenerationAgent(BaseAgent):
    """LangChain create_agent drafts WhatsApp text using tools; compliance already gated."""

    name = "MessageGenerationAgent"

    def __init__(self, llm: LLMProvider, db: Session | None = None) -> None:
        self.llm = llm
        self.db = db

    def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        profiles = {p["customerId"]: p for p in (state.get("candidateCustomers") or [])}
        recommendations = {r["customerId"]: r for r in (state.get("productRecommendations") or [])}
        eligibility = {r["customerId"]: r for r in (state.get("eligibilityResults") or [])}
        compliance = {r["customerId"]: r for r in (state.get("complianceResults") or [])}

        tools = build_crm_tools(self.db) if self.db is not None else None
        context_tool = tools["get_message_context"] if tools else None
        mock_llm = MockLLMProvider()

        drafts = []
        tools_used_all: list[str] = []
        execution_modes: list[str] = []

        for cid, profile in profiles.items():
            elig = eligibility.get(cid) or {}
            comp = compliance.get(cid) or {}
            rec = recommendations.get(cid) or {}
            # Deterministic gates — never let LLM override
            if not elig.get("overallPassed"):
                continue
            if not comp.get("contactAllowed"):
                continue
            if not rec.get("selected"):
                continue

            context = {
                "firstName": profile.get("firstName"),
                "productName": rec.get("productName"),
                "city": profile.get("city"),
                "segment": profile.get("customerSegment"),
            }
            fallback_body = mock_llm.generate_message(context)
            body = fallback_body
            execution = "mock_template"
            tools_used: list[str] = []

            if context_tool is not None:
                tool_json = invoke_tool(
                    context_tool,
                    first_name=str(context["firstName"] or "Customer"),
                    product_name=str(context["productName"] or "Personal Loan"),
                    city=str(context.get("city") or ""),
                    segment=str(context.get("segment") or ""),
                )
                tools_used.append("get_message_context")
                mock_responses = [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "get_message_context",
                                "args": {
                                    "first_name": context["firstName"],
                                    "product_name": context["productName"],
                                    "city": context.get("city") or "",
                                    "segment": context.get("segment") or "",
                                },
                                "id": f"msg_{cid[:8]}",
                            }
                        ],
                    ),
                    AIMessage(content=json.dumps({"body": fallback_body})),
                ]
                try:
                    agent_out = run_create_agent(
                        tools=[context_tool],
                        system_prompt=(
                            "You are the Message Generation Agent for banking WhatsApp outreach. "
                            "Call get_message_context, then draft ONE short compliant message. "
                            "No account numbers, balances, scores, or guaranteed approval. "
                            "Include STOP opt-out and demonstration disclaimer."
                        ),
                        user_prompt=(
                            f"Draft WhatsApp message using this tool context:\n{tool_json}"
                        ),
                        response_format=MessageDraftSchema,
                        purpose="message",
                        mock_responses=mock_responses,
                        agent_name="message_generation_agent",
                    )
                    body = (agent_out["payload"] or {}).get("body") or fallback_body
                    tools_used = list(dict.fromkeys(tools_used + agent_out["toolsCalled"]))
                    execution = agent_out["executionMode"]
                except Exception as exc:  # noqa: BLE001
                    try:
                        body = self.llm.generate_message(context)
                        execution = f"llm_direct_fallback:{type(exc).__name__}"
                    except Exception:  # noqa: BLE001
                        body = fallback_body
                        execution = f"mock_fallback:{type(exc).__name__}"
            else:
                body = self.llm.generate_message(context)
                execution = "llm_direct_no_db"

            body = validate_message_body(body, context=context)
            tools_used_all.extend(tools_used)
            execution_modes.append(execution)

            drafts.append(
                {
                    "customerId": cid,
                    "body": body,
                    "channel": (state.get("parsedIntent") or {}).get("channel", "WHATSAPP"),
                    "llmProviderUsed": getattr(self.llm, "name", "mock"),
                    "status": "DRAFT",
                    "agentFramework": "langchain.create_agent",
                    "toolsUsed": tools_used,
                    "executionMode": execution,
                    "validated": True,
                }
            )

        unique_tools = list(dict.fromkeys(tools_used_all))
        mode = execution_modes[0] if execution_modes else "none"
        return {
            "messageDrafts": drafts,
            "currentStep": self.name,
            "stepSummary": (
                f"Generated {len(drafts)} validated WhatsApp drafts via LangChain "
                f"({mode}); tools={unique_tools}"
            ),
            "processedRecords": len(drafts),
        }
