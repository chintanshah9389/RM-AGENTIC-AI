from __future__ import annotations

from datetime import date
from typing import Any


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _classify(score: float) -> str:
    if score < 40:
        return "LOW"
    if score < 70:
        return "MEDIUM"
    return "HIGH"


def compute_customer_value(profile: dict[str, Any]) -> dict[str, Any]:
    amb = float(profile.get("averageMonthlyBalance") or 0)
    balance_score = _clamp(amb / 2000)  # 200k AMB => 100

    salary_credits = int(profile.get("salaryCreditCount") or 0)
    salary_score = _clamp(salary_credits * 25)

    tenure_years = float(profile.get("tenureYears") or 0)
    tenure_score = _clamp(tenure_years * 12)

    holdings = len(profile.get("existingProducts") or [])
    product_score = _clamp(holdings * 25)

    txn_count = int(profile.get("transactionCount") or 0)
    txn_score = _clamp(txn_count * 8)

    engagement = float(profile.get("digitalEngagementScore") or 0)
    engagement_score = _clamp(engagement)

    overall = round(
        balance_score * 0.30
        + salary_score * 0.20
        + tenure_score * 0.15
        + product_score * 0.15
        + txn_score * 0.10
        + engagement_score * 0.10,
        2,
    )

    positives = []
    warnings = []
    if balance_score >= 70:
        positives.append("Strong average monthly balance")
    if salary_score >= 70:
        positives.append("Consistent salary credits")
    if tenure_score >= 70:
        positives.append("Long relationship tenure")
    if profile.get("dataQuality") == "INCOMPLETE_TXN":
        warnings.append("Incomplete transaction history — data quality warning")

    return {
        "overallScore": overall,
        "classification": _classify(overall),
        "componentScores": {
            "averageMonthlyBalance": round(balance_score, 2),
            "salaryConsistency": round(salary_score, 2),
            "relationshipTenure": round(tenure_score, 2),
            "productHoldings": round(product_score, 2),
            "transactionActivity": round(txn_score, 2),
            "digitalEngagement": round(engagement_score, 2),
        },
        "positiveFactors": positives,
        "warnings": warnings,
        "explanation": (
            f"Demonstration customer-value score {overall} "
            f"({_classify(overall)}). Weighted heuristic only."
        ),
    }


def compute_propensity(profile: dict[str, Any]) -> dict[str, Any]:
    salary_credits = int(profile.get("salaryCreditCount") or 0)
    salary_stability = _clamp(salary_credits * 25)

    purchase_txns = int(profile.get("relevantPurchaseCount") or 0)
    purchase_score = _clamp(purchase_txns * 15)

    has_credit = 80.0 if "CREDIT_CARD" in (profile.get("existingProducts") or []) or "LOAN" in (
        profile.get("existingProducts") or []
    ) else 35.0

    interested = 0
    for item in profile.get("campaignResponseHistory") or []:
        if str(item.get("response", "")).upper() == "INTERESTED":
            interested += 1
    interest_score = _clamp(40 + interested * 30)

    engagement = _clamp(float(profile.get("digitalEngagementScore") or 0))
    responsiveness = _clamp(interested * 40 + 20)
    tenure_score = _clamp(float(profile.get("tenureYears") or 0) * 12)

    overall = round(
        salary_stability * 0.25
        + purchase_score * 0.20
        + has_credit * 0.15
        + interest_score * 0.15
        + engagement * 0.10
        + responsiveness * 0.10
        + tenure_score * 0.05,
        2,
    )

    positives = []
    negatives = []
    if salary_stability >= 70:
        positives.append("Stable salary pattern")
    if interest_score >= 70:
        positives.append("Prior campaign interest")
    if has_credit < 50:
        negatives.append("Limited existing credit relationship")
    if engagement < 50:
        negatives.append("Lower digital engagement")

    warnings = []
    data_quality = "OK"
    if profile.get("dataQuality") == "INCOMPLETE_TXN":
        data_quality = "WARNING"
        warnings.append("Sparse transaction history reduces confidence")

    return {
        "overallScore": overall,
        "classification": _classify(overall),
        "componentScores": {
            "salaryStability": round(salary_stability, 2),
            "relevantPurchaseBehaviour": round(purchase_score, 2),
            "existingCreditRelationship": round(has_credit, 2),
            "productCampaignInterest": round(interest_score, 2),
            "digitalEngagement": round(engagement, 2),
            "previousCampaignResponsiveness": round(responsiveness, 2),
            "relationshipTenure": round(tenure_score, 2),
        },
        "positiveFactors": positives,
        "negativeFactors": negatives,
        "warnings": warnings,
        "dataQuality": data_quality,
        "explanation": (
            f"Demonstration heuristic propensity score {overall} ({_classify(overall)}). "
            "This is not a production credit, underwriting or lending model."
        ),
    }


def tenure_years(start: date, today: date | None = None) -> float:
    today = today or date.today()
    return max(0.0, (today - start).days / 365.25)
