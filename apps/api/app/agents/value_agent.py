from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.services.scoring import compute_customer_value


class CustomerValueAgent(BaseAgent):
    name = "CustomerValueAgent"

    def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        results = []
        for profile in state.get("candidateCustomers") or []:
            score = compute_customer_value(profile)
            results.append({"customerId": profile["customerId"], **score})
        high = sum(1 for r in results if r["classification"] == "HIGH")
        return {
            "customerValueResults": results,
            "currentStep": self.name,
            "stepSummary": f"Scored {len(results)} customers; {high} HIGH value",
            "processedRecords": len(results),
        }
