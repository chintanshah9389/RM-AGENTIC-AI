from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent


class ExplainabilityAgent(BaseAgent):
    name = "ExplainabilityAgent"

    def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        profiles = {p["customerId"]: p for p in (state.get("candidateCustomers") or [])}
        values = {r["customerId"]: r for r in (state.get("customerValueResults") or [])}
        props = {r["customerId"]: r for r in (state.get("propensityResults") or [])}
        recs = {r["customerId"]: r for r in (state.get("productRecommendations") or [])}
        eligs = {r["customerId"]: r for r in (state.get("eligibilityResults") or [])}
        comps = {r["customerId"]: r for r in (state.get("complianceResults") or [])}
        msgs = {m["customerId"]: m for m in (state.get("messageDrafts") or [])}

        explanations = []
        for cid, profile in profiles.items():
            value = values.get(cid) or {}
            prop = props.get(cid) or {}
            rec = recs.get(cid) or {}
            elig = eligs.get(cid) or {}
            comp = comps.get(cid) or {}
            msg = msgs.get(cid)

            required_action = "NONE"
            if comp.get("contactAllowed") and elig.get("overallPassed") and msg:
                required_action = "RM_REVIEW_AND_APPROVE"
            elif not comp.get("contactAllowed"):
                required_action = "NO_CONTACT_COMPLIANCE_BLOCK"
            elif not elig.get("overallPassed"):
                required_action = "NO_OFFER_INELIGIBLE"

            explanations.append(
                {
                    "customerId": cid,
                    "whySelected": (
                        f"{profile.get('fullName')} matches campaign filters as "
                        f"{profile.get('customerSegment')} in {profile.get('city')}."
                    ),
                    "whyValuable": value.get("explanation"),
                    "whyPropensity": prop.get("explanation"),
                    "whyProduct": rec.get("reason"),
                    "eligibilityPassed": [
                        r["ruleCode"] for r in (elig.get("rules") or []) if r.get("passed")
                    ],
                    "eligibilityFailed": [
                        r["ruleCode"] for r in (elig.get("rules") or []) if not r.get("passed")
                    ],
                    "complianceResult": comp.get("complianceStatus"),
                    "dataQuality": profile.get("dataQuality"),
                    "messageAvailable": bool(msg),
                    "requiredHumanAction": required_action,
                    "disclaimer": (
                        "Demonstration only. Scores, recommendations and offers do not represent "
                        "real lending or credit decisions."
                    ),
                }
            )

        return {
            "explanations": explanations,
            "currentStep": self.name,
            "stepSummary": f"Built explainability summaries for {len(explanations)} customers",
            "processedRecords": len(explanations),
        }
