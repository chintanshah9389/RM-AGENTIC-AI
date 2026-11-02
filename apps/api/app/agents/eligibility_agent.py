from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent


class EligibilityAgent(BaseAgent):
    name = "EligibilityAgent"

    def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        results = []
        for rec in state.get("productRecommendations") or []:
            eligibility = rec.get("eligibility") or {"overallPassed": False, "rules": [], "status": "INELIGIBLE"}
            results.append(
                {
                    "customerId": rec["customerId"],
                    "productId": rec.get("productId"),
                    "productName": rec.get("productName"),
                    "overallPassed": eligibility.get("overallPassed", False),
                    "status": eligibility.get("status", "INELIGIBLE"),
                    "rules": eligibility.get("rules", []),
                }
            )
        passed = sum(1 for r in results if r["overallPassed"])
        return {
            "eligibilityResults": results,
            "currentStep": self.name,
            "stepSummary": f"Eligibility evaluated; {passed}/{len(results)} passed",
            "processedRecords": len(results),
        }
