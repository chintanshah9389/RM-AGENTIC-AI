"""LangChain @tool wrappers over DB-backed CRM helpers."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import BaseTool, tool
from sqlalchemy.orm import Session

from app.tools.customer_tools import (
    get_active_products,
    get_customer_360_by_id,
    retrieve_candidate_customers,
)


def build_crm_tools(db: Session) -> dict[str, BaseTool]:
    """Build tools closed over the current DB session."""

    @tool
    def list_active_products() -> str:
        """List active bank products and their categories (source of truth for campaign product intent)."""
        products = get_active_products(db)
        compact = [
            {
                "productCode": p["productCode"],
                "name": p["name"],
                "category": p.get("category"),
                "minMonthlyIncome": p["minMonthlyIncome"],
                "interestRate": p["interestRate"],
            }
            for p in products
        ]
        categories = sorted(
            {str(p.get("category") or "").upper() for p in compact if p.get("category")}
        )
        return json.dumps(
            {
                "products": compact,
                "count": len(compact),
                "availableCategories": categories,
                "rule": "productCategory in intent MUST be one of availableCategories",
            }
        )

    @tool
    def search_customers(segment_hint: str = "HIGH_VALUE", min_income: float = 30000, limit: int = 20) -> str:
        """Search synthetic Customer360 candidates by segment hint and minimum income."""
        rows = retrieve_candidate_customers(
            db,
            segment_hint=segment_hint or "HIGH_VALUE",
            min_income=float(min_income or 30000),
            limit=int(limit or 20),
        )
        summary = [
            {
                "customerId": r["customerId"],
                "customerCode": r["customerCode"],
                "fullName": r["fullName"],
                "city": r["city"],
                "customerSegment": r["customerSegment"],
                "monthlyIncome": r["monthlyIncome"],
                "hasSalaryAccount": r["hasSalaryAccount"],
                "scenarioTag": r.get("scenarioTag"),
            }
            for r in rows
        ]
        return json.dumps({"customers": summary, "count": len(summary)})

    @tool
    def get_customer_360(customer_id: str) -> str:
        """Fetch one Customer360 profile by customerId (masked accounts, consent snapshot)."""
        profile = get_customer_360_by_id(db, customer_id)
        if not profile:
            return json.dumps({"error": "Customer not found", "customerId": customer_id})
        # Keep tool payload compact for the LLM
        compact = {
            "customerId": profile["customerId"],
            "customerCode": profile["customerCode"],
            "fullName": profile["fullName"],
            "firstName": profile["firstName"],
            "city": profile["city"],
            "customerSegment": profile["customerSegment"],
            "monthlyIncome": profile["monthlyIncome"],
            "hasSalaryAccount": profile["hasSalaryAccount"],
            "existingProducts": profile["existingProducts"],
            "consent": profile.get("consent"),
            "scenarioTag": profile.get("scenarioTag"),
        }
        return json.dumps(compact)

    @tool
    def get_message_context(
        first_name: str,
        product_name: str,
        city: str = "",
        segment: str = "",
    ) -> str:
        """Return allowed fields for drafting a WhatsApp promo (no balances/account numbers)."""
        return json.dumps(
            {
                "firstName": first_name,
                "productName": product_name,
                "city": city,
                "segment": segment,
                "rules": [
                    "Include STOP opt-out",
                    "Include eligibility disclaimer",
                    "No account numbers, balances, scores, or guaranteed approval",
                    "Mark as dummy demonstration data",
                ],
            }
        )

    return {
        "list_active_products": list_active_products,
        "search_customers": search_customers,
        "get_customer_360": get_customer_360,
        "get_message_context": get_message_context,
    }


def invoke_tool(tool_obj: BaseTool, **kwargs: Any) -> Any:
    """Invoke a LangChain tool with keyword args."""
    return tool_obj.invoke(kwargs)
