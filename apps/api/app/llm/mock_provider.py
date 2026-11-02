from __future__ import annotations

import re
from typing import Any

from app.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Deterministic offline LLM substitute. No API key required."""

    name = "mock"

    def parse_intent(self, request: str) -> dict[str, Any]:
        text = request.lower()
        # Do not default to Personal Loan — leave unresolved if request is ambiguous
        product = None
        if "car loan" in text or "auto loan" in text or "vehicle loan" in text:
            product = "CAR_LOAN"
        elif "gold loan" in text or "jewel" in text:
            product = "GOLD_LOAN"
        elif "education loan" in text or "student loan" in text:
            product = "EDUCATION_LOAN"
        elif "business loan" in text or "sme loan" in text:
            product = "BUSINESS_LOAN"
        elif "credit card" in text:
            product = "CREDIT_CARD"
        elif "home loan" in text or "housing" in text or "mortgage" in text:
            product = "HOME_LOAN"
        elif "personal loan" in text:
            product = "PERSONAL_LOAN"

        segment = "HIGH_VALUE"
        if "premium" in text:
            segment = "PREMIUM"
        elif "salary" in text:
            segment = "SALARY_ACCOUNT"
        elif "standard" in text:
            segment = "STANDARD"

        channel = "WHATSAPP" if "whatsapp" in text else "EMAIL" if "email" in text else "WHATSAPP"

        max_customers = 10
        match = re.search(r"(?:top|limit|max(?:imum)?)\s+(\d+)", text)
        if match:
            max_customers = int(match.group(1))

        payload = {
            "customerSegment": segment,
            "campaignPeriod": "CURRENT_MONTH",
            "channel": channel,
            "maximumCustomers": max_customers,
            "requiresMessageGeneration": "message" in text or "whatsapp" in text or True,
            "minValueScore": 70 if "high-value" in text or "high value" in text else 60,
            "minPropensityScore": 60 if "convert" in text or "propensity" in text else 50,
            "provider": self.name,
        }
        if product:
            payload["productCategory"] = product
        return payload

    def generate_message(self, context: dict[str, Any]) -> str:
        first = str(context.get("firstName") or "Customer")
        product = str(context.get("productName") or "our banking offer")
        return (
            f"Hello {first}, based on your relationship with Demo Bank, you may be interested in our "
            f"{product} option with flexible repayment tenures. Eligibility and terms apply. "
            f"Reply INTERESTED if you would like your Relationship Manager to contact you. "
            f"Reply STOP if you prefer not to receive promotional messages. "
            f"(Dummy demonstration data. Not a real bank offer.)"
        )

    def regenerate_message(self, context: dict[str, Any], instruction: str) -> str:
        base = self.generate_message(context)
        note = instruction.strip()[:120] if instruction else "more concise"
        return f"{base}\n\n[Regenerated with instruction: {note}]"

    def explain_recommendation(self, context: dict[str, Any]) -> str:
        name = context.get("customerName", "Customer")
        value = context.get("valueScore", 0)
        propensity = context.get("propensityScore", 0)
        product = context.get("productName") or "the requested product"
        return (
            f"{name} was selected using demonstration heuristics. "
            f"Customer value score {value} and conversion propensity {propensity} "
            f"supported recommending {product}. "
            f"Demonstration only. Scores do not represent real lending decisions."
        )
