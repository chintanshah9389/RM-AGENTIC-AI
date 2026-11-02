from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockLLMProvider


class NvidiaLLMProvider(LLMProvider):
    """NVIDIA API Catalog / NIM OpenAI-compatible chat provider with Mock fallback."""

    name = "nvidia"

    def __init__(self) -> None:
        self.settings = get_settings()
        self._fallback = MockLLMProvider()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.nvidia_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _chat(self, system: str, user: str, temperature: float = 0.2) -> str:
        if not self.settings.nvidia_api_key:
            raise RuntimeError("NVIDIA_API_KEY is not configured")

        payload = {
            "model": self.settings.nvidia_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": 600,
        }
        url = f"{self.settings.nvidia_base_url.rstrip('/')}/chat/completions"
        with httpx.Client(timeout=90.0) as client:
            response = client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()
        message = data["choices"][0]["message"]
        content = message.get("content")
        if not content:
            # Some NVIDIA reasoning models return reasoning_content only
            content = message.get("reasoning_content")
        if not content:
            raise ValueError("NVIDIA response contained no content")
        return str(content).strip()

    def parse_intent(self, request: str) -> dict[str, Any]:
        fallback = self._fallback.parse_intent(request)
        try:
            system = (
                "Extract banking CRM campaign intent. Reply with ONLY a JSON object. "
                "Use exactly these keys: "
                "productCategory (string code matching the request, e.g. PERSONAL_LOAN, "
                "CREDIT_CARD, HOME_LOAN, CAR_LOAN — or null if unclear; "
                "never invent a different product than the RM asked for), "
                "customerSegment (HIGH_VALUE|PREMIUM|STANDARD|SALARY_ACCOUNT), "
                "campaignPeriod (CURRENT_MONTH), "
                "channel (WHATSAPP|EMAIL), "
                "maximumCustomers (integer 1-50), "
                "requiresMessageGeneration (boolean), "
                "minValueScore (0-100 number), "
                "minPropensityScore (0-100 number). "
                "No markdown fences."
            )
            raw = self._chat(system, request, temperature=0.0)
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise ValueError("No JSON in NVIDIA response")
            parsed = json.loads(match.group(0))
            # Start from model output; do not seed Personal Loan from mock fallback
            normalized = {k: v for k, v in parsed.items() if v is not None}
            for key in (
                "customerSegment",
                "campaignPeriod",
                "channel",
                "maximumCustomers",
                "requiresMessageGeneration",
                "minValueScore",
                "minPropensityScore",
            ):
                if key not in normalized and key in fallback:
                    normalized[key] = fallback[key]
            # Light normalize only — final category is validated against catalogue in Intent agent
            product = str(normalized.get("productCategory", "")).upper().replace(" ", "_")
            if "CAR" in product or "AUTO" in product or "VEHICLE" in product:
                normalized["productCategory"] = "CAR_LOAN"
            elif "GOLD" in product or "JEWEL" in product:
                normalized["productCategory"] = "GOLD_LOAN"
            elif "EDUCATION" in product or "STUDENT" in product:
                normalized["productCategory"] = "EDUCATION_LOAN"
            elif "BUSINESS" in product or "SME" in product:
                normalized["productCategory"] = "BUSINESS_LOAN"
            elif "HOME" in product or "HOUSING" in product or "MORTGAGE" in product:
                normalized["productCategory"] = "HOME_LOAN"
            elif "CREDIT" in product:
                normalized["productCategory"] = "CREDIT_CARD"
            elif "PERSONAL" in product:
                normalized["productCategory"] = "PERSONAL_LOAN"
            elif product:
                normalized["productCategory"] = product
            else:
                # Preserve mock-detected category (e.g. CAR_LOAN) when model omitted it
                if fallback.get("productCategory"):
                    normalized["productCategory"] = fallback["productCategory"]
                else:
                    normalized.pop("productCategory", None)
            channel = str(normalized.get("channel", "")).upper()
            normalized["channel"] = "WHATSAPP" if "WHATSAPP" in channel else normalized.get("channel", "WHATSAPP")
            segment = str(normalized.get("customerSegment", "")).upper().replace(" ", "_").replace("-", "_")
            if "HIGH" in segment or "PREMIUM" in segment or "VALUE" in segment:
                normalized["customerSegment"] = "HIGH_VALUE"
            try:
                max_cust = int(float(normalized.get("maximumCustomers", fallback["maximumCustomers"])))
                normalized["maximumCustomers"] = max(1, min(50, max_cust if max_cust <= 50 else fallback["maximumCustomers"]))
            except (TypeError, ValueError):
                normalized["maximumCustomers"] = fallback["maximumCustomers"]
            for score_key in ("minValueScore", "minPropensityScore"):
                try:
                    score = float(normalized.get(score_key, fallback[score_key]))
                    if score <= 1:
                        score *= 100
                    normalized[score_key] = max(0, min(100, score))
                except (TypeError, ValueError):
                    normalized[score_key] = fallback[score_key]
            normalized["provider"] = self.name
            return normalized
        except Exception:
            result = dict(fallback)
            result["provider"] = "mock_fallback"
            result["nvidiaError"] = True
            return result

    def generate_message(self, context: dict[str, Any]) -> str:
        try:
            system = (
                "Generate a short compliant WhatsApp banking promotional message in plain text. "
                "Include first name, product name, eligibility disclaimer, next action, and STOP opt-out. "
                "Do not include account numbers, balances, scores, risk, guaranteed approval, emojis, or markdown."
            )
            user = json.dumps(context)
            text = self._chat(system, user, temperature=0.4)
            if "STOP" not in text.upper():
                text += " Reply STOP to opt out of promotional messages."
            if "Dummy demonstration" not in text:
                text += " (Dummy demonstration data. Not a real bank offer.)"
            return text
        except Exception:
            return self._fallback.generate_message(context)

    def regenerate_message(self, context: dict[str, Any], instruction: str) -> str:
        try:
            system = (
                "Regenerate a compliant WhatsApp banking promo message using the instruction. "
                "Keep disclaimers and STOP opt-out. No sensitive financial details."
            )
            user = json.dumps({"context": context, "instruction": instruction})
            return self._chat(system, user, temperature=0.4)
        except Exception:
            return self._fallback.regenerate_message(context, instruction)

    def explain_recommendation(self, context: dict[str, Any]) -> str:
        try:
            system = (
                "Write a concise business-friendly explanation for a banking RM. "
                "Base only on provided facts. No chain-of-thought. Mark as demonstration."
            )
            return self._chat(system, json.dumps(context), temperature=0.2)
        except Exception:
            return self._fallback.explain_recommendation(context)
