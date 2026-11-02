from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.services.compliance import evaluate_compliance


class ConsentComplianceAgent(BaseAgent):
    name = "ConsentComplianceAgent"

    def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        intent = state.get("parsedIntent") or {}
        channel = str(intent.get("channel") or "WHATSAPP")
        results = []
        for profile in state.get("candidateCustomers") or []:
            consent = profile.get("consent") or {}
            result = evaluate_compliance(consent, channel=channel)
            results.append({"customerId": profile["customerId"], **result})
        blocked = sum(1 for r in results if not r["contactAllowed"])
        return {
            "complianceResults": results,
            "currentStep": self.name,
            "stepSummary": f"Compliance checked; {blocked} blocked from contact",
            "processedRecords": len(results),
        }
