from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.services.scoring import compute_propensity


class ConversionPropensityAgent(BaseAgent):
    name = "ConversionPropensityAgent"

    def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        results = []
        for profile in state.get("candidateCustomers") or []:
            score = compute_propensity(profile)
            results.append({"customerId": profile["customerId"], **score})
        high = sum(1 for r in results if r["classification"] == "HIGH")
        return {
            "propensityResults": results,
            "currentStep": self.name,
            "stepSummary": (
                f"Computed propensity for {len(results)} customers; {high} HIGH. "
                "Demonstration heuristic only."
            ),
            "processedRecords": len(results),
        }
