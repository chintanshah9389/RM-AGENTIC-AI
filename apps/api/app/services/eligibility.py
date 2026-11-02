from __future__ import annotations

from typing import Any


RISK_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def evaluate_eligibility(customer: dict[str, Any], product: dict[str, Any], value_score: float) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []

    def add(code: str, name: str, passed: bool, observed: Any, required: Any, reason: str) -> None:
        rules.append(
            {
                "ruleCode": code,
                "ruleName": name,
                "passed": passed,
                "observedValue": observed,
                "requiredValue": required,
                "reason": reason,
            }
        )

    active = bool(customer.get("isActive", True))
    add(
        "CUSTOMER_ACTIVE",
        "Customer is active",
        active,
        active,
        True,
        "Customer is active." if active else "Customer is inactive.",
    )

    age = int(customer.get("age") or 0)
    age_ok = 21 <= age <= 65
    add(
        "AGE_ALLOWED",
        "Age within allowed range",
        age_ok,
        age,
        "21-65",
        "Age is within policy range." if age_ok else "Age outside allowed lending range.",
    )

    income = float(customer.get("monthlyIncome") or 0)
    min_income = float(product.get("minMonthlyIncome") or 0)
    income_ok = income >= min_income
    add(
        "MINIMUM_INCOME",
        "Minimum monthly income",
        income_ok,
        income,
        min_income,
        "Monthly income satisfies product requirement."
        if income_ok
        else "Monthly income below product minimum.",
    )

    risk = str(customer.get("riskCategory") or "HIGH")
    max_risk = str(product.get("maxRiskCategory") or "MEDIUM")
    risk_ok = RISK_ORDER.get(risk, 99) <= RISK_ORDER.get(max_risk, 2)
    add(
        "MAXIMUM_RISK_LEVEL",
        "Maximum risk level",
        risk_ok,
        risk,
        max_risk,
        "Risk category acceptable." if risk_ok else "Risk category exceeds product threshold.",
    )

    delinquency = int(customer.get("maxDelinquencyDays") or 0)
    del_ok = delinquency < 60
    add(
        "NO_SEVERE_DELINQUENCY",
        "No severe delinquency",
        del_ok,
        delinquency,
        "<60 days",
        "No severe delinquency detected." if del_ok else "Severe delinquency present.",
    )

    if product.get("requiresSalaryAccount"):
        has_salary = bool(customer.get("hasSalaryAccount"))
        add(
            "SALARY_ACCOUNT_REQUIRED",
            "Salary account required",
            has_salary,
            has_salary,
            True,
            "Salary account present." if has_salary else "Salary account required but missing.",
        )
        min_salary = float(product.get("minSalaryAmount") or 0)
        if min_salary:
            salary_ok = income >= min_salary
            add(
                "MINIMUM_SALARY_AMOUNT",
                "Minimum salary amount",
                salary_ok,
                income,
                min_salary,
                "Salary meets product minimum." if salary_ok else "Salary below product minimum.",
            )

    min_value = product.get("minCustomerValueScore")
    if min_value is not None:
        value_ok = value_score >= float(min_value)
        add(
            "MINIMUM_CUSTOMER_VALUE",
            "Minimum customer value score",
            value_ok,
            value_score,
            min_value,
            "Customer value meets product threshold."
            if value_ok
            else "Customer value below product threshold.",
        )

    overall = all(r["passed"] for r in rules)
    return {
        "overallPassed": overall,
        "rules": rules,
        "status": "ELIGIBLE" if overall else "INELIGIBLE",
    }
