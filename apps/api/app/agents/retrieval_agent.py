from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.lc_runner import run_create_agent
from app.agents.schemas import RetrievalPlanSchema
from app.agents.validation import validate_candidates
from app.tools.customer_tools import retrieve_candidate_customers
from app.tools.langchain_tools import build_crm_tools, invoke_tool


class CustomerRetrievalAgent(BaseAgent):
    """LangChain create_agent plans filters; search_customers tool is source of truth."""

    name = "CustomerRetrievalAgent"

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        intent = state.get("parsedIntent") or {}
        limit = int(intent.get("maximumCustomers") or state.get("maxCustomers") or 10)
        pool_limit = max(limit * 2, 15)
        segment_hint = str(intent.get("customerSegment") or "HIGH_VALUE")
        min_income = 30000.0

        tools = build_crm_tools(self.db)
        search_tool = tools["search_customers"]
        execution = "tool_direct"
        tools_used = ["search_customers"]
        plan: dict[str, Any] = {
            "segmentHint": segment_hint,
            "minIncome": min_income,
            "limit": pool_limit,
        }

        mock_responses = [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "search_customers",
                        "args": {
                            "segment_hint": segment_hint,
                            "min_income": min_income,
                            "limit": pool_limit,
                        },
                        "id": "retrieval_search",
                    }
                ],
            ),
            AIMessage(
                content=json.dumps(
                    {
                        "segmentHint": segment_hint,
                        "minIncome": min_income,
                        "limit": pool_limit,
                        "notes": "Prefer high-income / planted scenarios",
                    }
                )
            ),
        ]

        try:
            agent_out = run_create_agent(
                tools=[search_tool],
                system_prompt=(
                    "You are the Customer Retrieval Agent. "
                    "You MUST call search_customers with sensible filters. "
                    "Never invent customer IDs. After the tool returns, summarize the plan."
                ),
                user_prompt=(
                    f"Parsed intent: {json.dumps(intent)}\n"
                    f"Retrieve up to {pool_limit} candidates for Personal Loan outreach."
                ),
                response_format=RetrievalPlanSchema,
                purpose="retrieval",
                mock_responses=mock_responses,
                agent_name="customer_retrieval_agent",
            )
            plan.update(agent_out["payload"] or {})
            tools_used = list(dict.fromkeys(tools_used + agent_out["toolsCalled"]))
            execution = agent_out["executionMode"]
            # Re-run tool with validated plan so DB is always source of truth
            segment_hint = str(plan.get("segmentHint") or segment_hint)
            try:
                min_income = float(plan.get("minIncome") or min_income)
            except (TypeError, ValueError):
                min_income = 30000.0
            try:
                pool_limit = int(plan.get("limit") or pool_limit)
            except (TypeError, ValueError):
                pool_limit = max(limit * 2, 15)
            pool_limit = max(1, min(100, pool_limit))
        except Exception as exc:  # noqa: BLE001
            execution = f"tool_direct_fallback:{type(exc).__name__}"

        # System of record: candidates only from DB tool / helper
        tool_json = invoke_tool(
            search_tool,
            segment_hint=segment_hint,
            min_income=min_income,
            limit=pool_limit,
        )
        try:
            tool_payload = json.loads(tool_json)
            allowed_ids = {row["customerId"] for row in tool_payload.get("customers") or []}
        except json.JSONDecodeError:
            allowed_ids = set()

        candidates = retrieve_candidate_customers(
            self.db,
            segment_hint=segment_hint,
            min_income=min_income,
            limit=pool_limit,
        )
        candidates = validate_candidates(
            candidates, allowed_ids=allowed_ids or None, limit=pool_limit
        )

        return {
            "candidateCustomers": candidates,
            "retrievalPlan": {
                **plan,
                "segmentHint": segment_hint,
                "minIncome": min_income,
                "limit": pool_limit,
                "agentFramework": "langchain.create_agent",
                "toolsUsed": tools_used,
                "executionMode": execution,
            },
            "currentStep": self.name,
            "stepSummary": (
                f"Retrieved {len(candidates)} Customer360 profiles via LangChain tools "
                f"({execution}); segment={segment_hint}"
            ),
            "processedRecords": len(candidates),
        }
