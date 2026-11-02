from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.services.recommendation import recommend_product
from app.tools.customer_tools import get_active_products


class ProductRecommendationAgent(BaseAgent):
    name = "ProductRecommendationAgent"

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        products = get_active_products(self.db)
        intent = state.get("parsedIntent") or {}
        category = intent.get("productCategory")
        value_map = {
            r["customerId"]: r["overallScore"] for r in (state.get("customerValueResults") or [])
        }
        recommendations = []
        for profile in state.get("candidateCustomers") or []:
            cid = profile["customerId"]
            if not category:
                recommendations.append(
                    {
                        "customerId": cid,
                        "selected": False,
                        "productId": None,
                        "productCode": None,
                        "productName": None,
                        "matchScore": 0,
                        "reason": (
                            "Intent agent could not resolve a product category from the "
                            "campaign request against the live catalogue."
                        ),
                        "disclaimer": "Dummy demonstration data. Not a real bank offer.",
                    }
                )
                continue
            rec = recommend_product(
                profile,
                products,
                value_map.get(cid, 0),
                product_category=str(category),
            )
            recommendations.append({"customerId": cid, **rec})
        selected = sum(1 for r in recommendations if r.get("selected"))
        label = category or "UNRESOLVED"
        return {
            "productRecommendations": recommendations,
            "currentStep": self.name,
            "stepSummary": (
                f"Generated {label} recommendations; {selected} selected "
                f"(filtered by Intent agent category, not form defaults)"
            ),
            "processedRecords": len(recommendations),
        }
