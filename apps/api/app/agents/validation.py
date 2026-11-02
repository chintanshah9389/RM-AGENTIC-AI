"""Post-LLM validators — catalogue + request grounding win over model guesses."""

from __future__ import annotations

import re
from typing import Any


CHANNELS = {"WHATSAPP", "EMAIL"}
SEGMENTS = {
    "HIGH_VALUE",
    "PREMIUM",
    "STANDARD",
    "SALARY_ACCOUNT",
    "PRIVATE",
    "GOLD",
}

# Known request language → canonical category code (must exist in catalogue to proceed)
REQUEST_PRODUCT_HINTS: list[tuple[tuple[str, ...], str]] = [
    (("car loan", "auto loan", "vehicle loan", "two wheeler", "car_loan", "auto_loan"), "CAR_LOAN"),
    (("home loan", "housing loan", "mortgage", "home_loan"), "HOME_LOAN"),
    (("credit card", "credit_card"), "CREDIT_CARD"),
    (("personal loan", "personal_loan"), "PERSONAL_LOAN"),
    (("salary loan", "salary advantage"), "PERSONAL_LOAN"),
    (("gold loan", "gold_loan", "jewel loan", "jewellery loan", "jewelry loan"), "GOLD_LOAN"),
    (("education loan", "student loan", "education_loan"), "EDUCATION_LOAN"),
    (("business loan", "sme loan", "business_loan"), "BUSINESS_LOAN"),
]

# Phrases that mean the RM named a product — never ignore these for an LLM substitute
_PRODUCT_SIGNAL = re.compile(
    r"\b("
    r"gold\s+loan|jewel(?:lery|ry)?\s+loan|education\s+loan|student\s+loan|"
    r"business\s+loan|sme\s+loan|car\s+loan|auto\s+loan|vehicle\s+loan|"
    r"home\s+loan|housing\s+loan|personal\s+loan|salary\s+loan|credit\s+card|"
    r"[a-z][a-z0-9]+\s+loan"
    r")\b",
    re.IGNORECASE,
)


def _normalize_token(value: str) -> str:
    return str(value or "").upper().replace(" ", "_").replace("-", "_")


def detect_requested_product(request_text: str) -> str | None:
    """Detect what product the RM asked for from natural language (independent of catalogue)."""
    text = (request_text or "").lower()
    for needles, category in REQUEST_PRODUCT_HINTS:
        if any(n in text for n in needles):
            return category

    # Any "<name> loan" (e.g. tractor loan) → that family; do NOT map to Personal Loan
    match = _PRODUCT_SIGNAL.search(text)
    if match:
        phrase = re.sub(r"\s+", " ", match.group(1).strip().lower())
        if phrase == "credit card":
            return "CREDIT_CARD"
        return _normalize_token(phrase)

    # Generic bare "loan" alone is ambiguous — do not guess Personal Loan
    return None


def resolve_product_category(
    raw_category: Any,
    *,
    request_text: str,
    catalogue_categories: list[str] | set[str] | None,
) -> tuple[str | None, str]:
    """Resolve product category. Never invent a catalogue product the request did not ask for."""
    catalogue = {
        _normalize_token(c)
        for c in (catalogue_categories or [])
        if _normalize_token(c)
    }
    requested = detect_requested_product(request_text)
    raw = _normalize_token(raw_category)

    # 1) RM asked for a specific product family
    if requested:
        if catalogue and requested in catalogue:
            return requested, "request_catalogue_match"
        # Asked for something we do not sell — do NOT substitute Personal Loan
        return None, f"not_in_catalogue:{requested}"

    # 2) Request named some product-like phrase but detector returned None — still block LLM swap
    if _PRODUCT_SIGNAL.search(request_text or ""):
        return None, "product_named_but_unresolved"

    # 3) No clear product in text — only accept LLM if it matches catalogue exactly
    if raw and catalogue and raw in catalogue:
        return raw, "llm_catalogue_match"

    if raw and not catalogue:
        return raw, "llm_unvalidated"

    # 4) Try matching catalogue category names mentioned loosely in text
    text = (request_text or "").lower()
    for cat in catalogue:
        pretty = cat.replace("_", " ").lower()
        if pretty in text or cat.lower() in text:
            return cat, "request_text_catalogue_match"

    return None, "unresolved"

def validate_intent(
    raw: dict[str, Any],
    *,
    fallback: dict[str, Any],
    request_text: str = "",
    catalogue_categories: list[str] | None = None,
) -> dict[str, Any]:
    out = dict(fallback)
    out.update({k: v for k, v in (raw or {}).items() if v is not None})

    requested = detect_requested_product(request_text)
    category, category_source = resolve_product_category(
        out.get("productCategory"),
        request_text=request_text,
        catalogue_categories=catalogue_categories,
    )
    out["requestedProductCategory"] = requested
    out["productCategory"] = category
    out["productCategorySource"] = category_source
    out["productCategoryResolved"] = category is not None
    out["productAvailable"] = category is not None
    if catalogue_categories:
        out["availableProductCategories"] = sorted(
            {_normalize_token(c) for c in catalogue_categories if c}
        )

    if not category:
        # Prefer what the RM typed — never surface a substituted LLM product (e.g. Personal Loan)
        missing = requested or detect_requested_product(request_text) or "requested product"
        label = str(missing).replace("_", " ").title()
        available = ", ".join(out.get("availableProductCategories") or []) or "none"
        out["productUnavailableMessage"] = (
            f"No data found for {label}. "
            f"This product is not in the catalogue/database. "
            f"Available catalogue: {available}."
        )
        out["requestedProductCategory"] = requested or detect_requested_product(request_text)

    segment = _normalize_token(out.get("customerSegment", ""))
    if segment not in SEGMENTS:
        if "SALARY" in segment:
            segment = "SALARY_ACCOUNT"
        elif "HIGH" in segment or "VALUE" in segment:
            segment = "HIGH_VALUE"
        elif "PREMIUM" in segment:
            segment = "PREMIUM"
        elif "PRIVATE" in segment:
            segment = "PRIVATE"
        elif "GOLD" in segment:
            segment = "GOLD"
        else:
            rt = (request_text or "").lower()
            if "salary" in rt:
                segment = "SALARY_ACCOUNT"
            elif "premium" in rt:
                segment = "PREMIUM"
            elif "private" in rt:
                segment = "PRIVATE"
            else:
                segment = "HIGH_VALUE"
    out["customerSegment"] = segment

    channel = _normalize_token(out.get("channel", ""))
    rt = (request_text or "").lower()
    if "whatsapp" in rt:
        channel = "WHATSAPP"
    elif "email" in rt and "whatsapp" not in rt:
        channel = "EMAIL"
    elif "WHATSAPP" in channel:
        channel = "WHATSAPP"
    elif "EMAIL" in channel:
        channel = "EMAIL"
    if channel not in CHANNELS:
        channel = "WHATSAPP"
    out["channel"] = channel

    try:
        max_c = int(float(out.get("maximumCustomers", fallback.get("maximumCustomers", 10))))
        out["maximumCustomers"] = max(1, min(50, max_c))
    except (TypeError, ValueError):
        out["maximumCustomers"] = fallback.get("maximumCustomers", 10)

    for key in ("minValueScore", "minPropensityScore"):
        try:
            score = float(out.get(key, fallback.get(key, 60)))
            if score <= 1:
                score *= 100
            out[key] = max(0.0, min(100.0, score))
        except (TypeError, ValueError):
            out[key] = fallback.get(key, 60)

    out["campaignPeriod"] = "CURRENT_MONTH"
    out["requiresMessageGeneration"] = bool(out.get("requiresMessageGeneration", True))
    out["validated"] = True
    return out


def validate_candidates(
    candidates: list[dict[str, Any]],
    *,
    allowed_ids: set[str] | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in candidates or []:
        cid = str(row.get("customerId") or "")
        if not cid or cid in seen:
            continue
        if allowed_ids is not None and cid not in allowed_ids:
            continue
        seen.add(cid)
        cleaned.append(row)
        if len(cleaned) >= max(1, limit):
            break
    return cleaned


def validate_message_body(body: str, *, context: dict[str, Any]) -> str:
    text = (body or "").strip()
    first = str(context.get("firstName") or "Customer")
    product = str(context.get("productName") or "our banking offer")

    if len(text) < 40:
        text = (
            f"Hello {first}, based on your relationship with Demo Bank, you may be interested "
            f"in {product}. Eligibility and terms apply. Reply INTERESTED to talk "
            f"to your Relationship Manager. Reply STOP to opt out. "
            f"(Dummy demonstration data. Not a real bank offer.)"
        )

    text = re.sub(r"\b\d{9,}\b", "[REDACTED]", text)
    text = re.sub(r"(?i)guaranteed approval", "subject to eligibility", text)

    if "STOP" not in text.upper():
        text += " Reply STOP to opt out of promotional messages."
    if "Dummy demonstration" not in text and "demonstration" not in text.lower():
        text += " (Dummy demonstration data. Not a real bank offer.)"
    if "eligib" not in text.lower() and "terms apply" not in text.lower():
        text += " Eligibility and terms apply."

    if product and product.lower() not in text.lower() and product != "our banking offer":
        text = f"{text} Product referenced: {product}."

    return text.strip()
