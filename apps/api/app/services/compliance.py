from __future__ import annotations

from typing import Any


def evaluate_compliance(consent: dict[str, Any], channel: str = "WHATSAPP") -> dict[str, Any]:
    failed: list[str] = []
    warnings: list[str] = []
    details: dict[str, Any] = {
        "marketingConsent": bool(consent.get("marketingConsent")),
        "whatsappConsent": bool(consent.get("whatsappConsent")),
        "doNotContact": bool(consent.get("doNotContact")),
        "contactsThisMonth": int(consent.get("contactsThisMonth") or 0),
        "maximumContactsPerMonth": int(consent.get("maximumContactsPerMonth") or 0),
        "channel": channel,
    }

    if consent.get("doNotContact"):
        failed.append("DO_NOT_CONTACT")
    if not consent.get("marketingConsent"):
        failed.append("MARKETING_CONSENT")
    if channel.upper() == "WHATSAPP" and not consent.get("whatsappConsent"):
        failed.append("WHATSAPP_CONSENT")

    contacts = int(consent.get("contactsThisMonth") or 0)
    maximum = int(consent.get("maximumContactsPerMonth") or 0)
    if maximum and contacts >= maximum:
        failed.append("CONTACT_FREQUENCY_LIMIT")

    if failed:
        status = "BLOCKED"
        contact_allowed = False
        explanation = (
            "Compliance blocked outbound communication. "
            f"Failed checks: {', '.join(failed)}. "
            "Compliance always overrides commercial scores."
        )
    else:
        status = "PASSED"
        contact_allowed = True
        explanation = "Customer passed consent and communication compliance checks."

    if contacts == maximum - 1 and contact_allowed:
        warnings.append("Approaching monthly contact limit")

    return {
        "complianceStatus": status,
        "contactAllowed": contact_allowed,
        "failedChecks": failed,
        "warnings": warnings,
        "explanation": explanation,
        "details": details,
    }
