from __future__ import annotations

from typing import Any

from app.services.eligibility import evaluate_eligibility


def recommend_product(
    customer: dict[str, Any],
    products: list[dict[str, Any]],
    value_score: float,
    product_category: str | None = None,
) -> dict[str, Any]:
    """Evaluate products and pick the best eligible option for the requested category."""

    if not product_category:
        return {
            "selected": False,
            "productId": None,
            "productCode": None,
            "productName": None,
            "matchScore": 0,
            "reason": "Missing product category from Intent agent.",
            "indicativeAmountMin": None,
            "indicativeAmountMax": None,
            "indicativeRate": None,
            "tenureMin": None,
            "tenureMax": None,
            "conditions": [],
            "eligibility": {"overallPassed": False, "rules": []},
            "allEvaluations": [],
            "disclaimer": "Dummy demonstration data. Not a real bank offer.",
        }

    category = str(product_category).upper()
    scoped = [p for p in products if str(p.get("category") or "").upper() == category]
    if not scoped:
        return {
            "selected": False,
            "productId": None,
            "productCode": None,
            "productName": None,
            "matchScore": 0,
            "reason": (
                f"No active products found for category {category}. "
                "Campaign intent does not match the product catalogue."
            ),
            "indicativeAmountMin": None,
            "indicativeAmountMax": None,
            "indicativeRate": None,
            "tenureMin": None,
            "tenureMax": None,
            "conditions": [f"Requested category: {category}"],
            "eligibility": {"overallPassed": False, "rules": []},
            "allEvaluations": [],
            "disclaimer": "Dummy demonstration data. Not a real bank offer.",
        }

    evaluations: list[dict[str, Any]] = []
    for product in scoped:
        eligibility = evaluate_eligibility(customer, product, value_score)
        match = 0.0
        if eligibility["overallPassed"]:
            match = 60.0
            code = str(product.get("productCode") or "")
            name = str(product.get("name") or "").upper()
            if code.endswith("_PREMIUM") or "PREMIUM" in name:
                match += 25
            elif code.endswith("_SALARY") or "SALARY" in name:
                match += 15
            else:
                match += 10
            match += min(15.0, value_score / 10)
        evaluations.append(
            {
                "product": product,
                "eligibility": eligibility,
                "matchScore": round(match, 2),
            }
        )

    eligible = [e for e in evaluations if e["eligibility"]["overallPassed"]]
    if not eligible:
        # Prefer showing best attempted premium/standard with failure reason
        best_attempt = sorted(evaluations, key=lambda e: e["matchScore"], reverse=True)[0]
        product = best_attempt["product"]
        return {
            "selected": False,
            "productId": product["id"],
            "productCode": product["productCode"],
            "productName": product["name"],
            "matchScore": best_attempt["matchScore"],
            "reason": f"No {category.replace('_', ' ').title()} product fully eligible under dummy rules.",
            "indicativeAmountMin": product["amountMin"],
            "indicativeAmountMax": product["amountMax"],
            "indicativeRate": product["interestRate"],
            "tenureMin": product["tenureMinMonths"],
            "tenureMax": product["tenureMaxMonths"],
            "conditions": ["Eligibility failed under demonstration rules"],
            "eligibility": best_attempt["eligibility"],
            "allEvaluations": evaluations,
            "disclaimer": "Dummy demonstration data. Not a real bank offer.",
        }

    best = sorted(eligible, key=lambda e: e["matchScore"], reverse=True)[0]
    product = best["product"]
    reason = (
        f"{product['name']} selected because customer income and customer-value score "
        f"satisfy the dummy product thresholds."
    )
    if product.get("productCode") == "PL_STANDARD":
        premium = next((e for e in evaluations if e["product"].get("productCode") == "PL_PREMIUM"), None)
        if premium and not premium["eligibility"]["overallPassed"]:
            reason = (
                "Premium Personal Loan rejected on income/value thresholds; "
                "Standard Personal Loan selected as eligible alternative."
            )

    return {
        "selected": True,
        "productId": product["id"],
        "productCode": product["productCode"],
        "productName": product["name"],
        "matchScore": best["matchScore"],
        "reason": reason,
        "indicativeAmountMin": product["amountMin"],
        "indicativeAmountMax": product["amountMax"],
        "indicativeRate": product["interestRate"],
        "tenureMin": product["tenureMinMonths"],
        "tenureMax": product["tenureMaxMonths"],
        "conditions": [
            f"Min income INR {product['minMonthlyIncome']:,.0f}",
            "Eligibility and terms apply",
        ],
        "eligibility": best["eligibility"],
        "allEvaluations": [
            {
                "productCode": e["product"]["productCode"],
                "passed": e["eligibility"]["overallPassed"],
                "matchScore": e["matchScore"],
            }
            for e in evaluations
        ],
        "disclaimer": "Dummy demonstration data. Not a real bank offer.",
    }
