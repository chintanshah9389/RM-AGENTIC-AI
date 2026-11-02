from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.lc_runner import run_create_agent
from app.agents.schemas import IntentSchema
from app.agents.validation import validate_intent
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.tools.customer_tools import get_active_products
from app.tools.langchain_tools import build_crm_tools, invoke_tool


class IntentUnderstandingAgent(BaseAgent):
    """LangChain create_agent + catalogue tools; product/channel come from request + LLM."""

    name = "IntentUnderstandingAgent"

    def __init__(self, llm: LLMProvider, db: Session | None = None) -> None:
        self.llm = llm
        self.db = db

    def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        request = state.get("originalRequest") or ""
        fallback = MockLLMProvider().parse_intent(request)
        if state.get("minValueScore") is not None:
            fallback["minValueScore"] = state["minValueScore"]
        if state.get("minPropensityScore") is not None:
            fallback["minPropensityScore"] = state["minPropensityScore"]
        if state.get("maxCustomers") is not None:
            fallback["maximumCustomers"] = state["maxCustomers"]

        tools_meta: list[str] = []
        execution = "fallback"
        raw: dict[str, Any] = {}
        catalogue_categories: list[str] = []

        if self.db is not None:
            products = get_active_products(self.db)
            catalogue_categories = sorted(
                {str(p.get("category") or "").upper() for p in products if p.get("category")}
            )
            tools = build_crm_tools(self.db)
            product_tool = tools["list_active_products"]
            product_json = invoke_tool(product_tool)
            tools_meta.append("list_active_products")

            # Ground mock agent final answer on catalogue + request (not a fixed product)
            grounded_fallback = dict(fallback)
            grounded_fallback["productCategory"] = fallback.get("productCategory")
            grounded_fallback["availableCategories"] = catalogue_categories

            mock_responses = [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "list_active_products",
                            "args": {},
                            "id": "intent_products",
                        }
                    ],
                ),
                AIMessage(content=json.dumps(grounded_fallback)),
            ]
            try:
                agent_out = run_create_agent(
                    tools=[product_tool],
                    system_prompt=(
                        "You are the Intent Understanding Agent for a banking CRM. "
                        "Always call list_active_products first. "
                        "Set productCategory ONLY if the RM request matches one availableCategories value. "
                        "If the request asks for a product not in availableCategories "
                        "(example: Car Loan when catalogue has no CAR_LOAN), omit productCategory "
                        "or set it to the requested code that is missing — do NOT substitute Personal Loan. "
                        "Never invent a different product just to fill the field. "
                        "Set channel from the request (WHATSAPP or EMAIL)."
                    ),
                    user_prompt=(
                        f"RM request:\n{request}\n\n"
                        f"Product catalogue tool output:\n{product_json}\n\n"
                        "Return JSON intent. If the requested product is not in availableCategories, "
                        "do not pick Personal Loan as a stand-in."
                    ),
                    response_format=IntentSchema,
                    purpose="intent",
                    mock_responses=mock_responses,
                    agent_name="intent_understanding_agent",
                )
                raw = agent_out["payload"]
                tools_meta = list(dict.fromkeys(tools_meta + agent_out["toolsCalled"]))
                execution = agent_out["executionMode"]
            except Exception as exc:  # noqa: BLE001
                try:
                    raw = self.llm.parse_intent(request)
                    execution = f"llm_direct_fallback:{type(exc).__name__}"
                except Exception:  # noqa: BLE001
                    raw = fallback
                    execution = f"mock_fallback:{type(exc).__name__}"
        else:
            raw = self.llm.parse_intent(request)
            execution = "llm_direct_no_db"

        # Campaign form may send AUTO — ignore it; agents own product/channel
        if str(raw.get("productCategory") or "").upper() in {"AUTO", "UNRESOLVED", "NONE", ""}:
            raw.pop("productCategory", None)

        parsed = validate_intent(
            raw,
            fallback=fallback,
            request_text=request,
            catalogue_categories=catalogue_categories or None,
        )
        parsed["provider"] = getattr(self.llm, "name", "unknown")
        parsed["agentFramework"] = "langchain.create_agent"
        parsed["toolsUsed"] = tools_meta
        parsed["executionMode"] = execution

        unresolved = not parsed.get("productCategoryResolved")
        summary = (
            f"Intent via LangChain agent ({execution}); "
            f"product={parsed.get('productCategory') or 'UNRESOLVED'} "
            f"({parsed.get('productCategorySource')}); "
            f"channel={parsed.get('channel')}; tools={tools_meta}"
        )
        if unresolved:
            summary += " — no catalogue category matched; recommendations may be empty"

        return {
            "parsedIntent": parsed,
            "currentStep": self.name,
            "stepSummary": summary,
        }
