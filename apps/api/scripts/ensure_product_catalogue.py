"""Upsert missing product categories without reseeding all customers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Product

CATALOGUE = [
    {
        "product_code": "PL_STANDARD",
        "name": "Personal Loan Standard",
        "category": "PERSONAL_LOAN",
        "min_monthly_income": 30000,
        "min_customer_value_score": None,
        "requires_salary_account": False,
        "min_salary_amount": None,
        "amount_min": 50000,
        "amount_max": 500000,
        "interest_rate": 12.50,
        "tenure_min_months": 12,
        "tenure_max_months": 48,
        "max_risk_category": "MEDIUM",
    },
    {
        "product_code": "PL_PREMIUM",
        "name": "Personal Loan Premium",
        "category": "PERSONAL_LOAN",
        "min_monthly_income": 75000,
        "min_customer_value_score": 70,
        "requires_salary_account": False,
        "min_salary_amount": None,
        "amount_min": 200000,
        "amount_max": 1500000,
        "interest_rate": 10.75,
        "tenure_min_months": 12,
        "tenure_max_months": 60,
        "max_risk_category": "MEDIUM",
    },
    {
        "product_code": "PL_SALARY",
        "name": "Salary Advantage Loan",
        "category": "PERSONAL_LOAN",
        "min_monthly_income": 40000,
        "min_customer_value_score": None,
        "requires_salary_account": True,
        "min_salary_amount": 40000,
        "amount_min": 100000,
        "amount_max": 800000,
        "interest_rate": 11.25,
        "tenure_min_months": 12,
        "tenure_max_months": 48,
        "max_risk_category": "MEDIUM",
    },
    {
        "product_code": "HL_STANDARD",
        "name": "Home Loan Standard",
        "category": "HOME_LOAN",
        "min_monthly_income": 50000,
        "min_customer_value_score": 60,
        "requires_salary_account": False,
        "min_salary_amount": None,
        "amount_min": 1000000,
        "amount_max": 10000000,
        "interest_rate": 8.75,
        "tenure_min_months": 60,
        "tenure_max_months": 300,
        "max_risk_category": "MEDIUM",
    },
    {
        "product_code": "HL_PREMIUM",
        "name": "Home Loan Premium",
        "category": "HOME_LOAN",
        "min_monthly_income": 100000,
        "min_customer_value_score": 75,
        "requires_salary_account": False,
        "min_salary_amount": None,
        "amount_min": 2500000,
        "amount_max": 25000000,
        "interest_rate": 8.25,
        "tenure_min_months": 60,
        "tenure_max_months": 360,
        "max_risk_category": "MEDIUM",
    },
    {
        "product_code": "CC_STANDARD",
        "name": "Classic Credit Card",
        "category": "CREDIT_CARD",
        "min_monthly_income": 25000,
        "min_customer_value_score": None,
        "requires_salary_account": False,
        "min_salary_amount": None,
        "amount_min": 25000,
        "amount_max": 200000,
        "interest_rate": 36.0,
        "tenure_min_months": 1,
        "tenure_max_months": 12,
        "max_risk_category": "MEDIUM",
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        created = 0
        updated = 0
        for spec in CATALOGUE:
            existing = db.scalar(
                select(Product).where(Product.product_code == spec["product_code"])
            )
            if existing:
                for key, value in spec.items():
                    setattr(existing, key, value)
                existing.is_active = True
                updated += 1
            else:
                db.add(Product(**spec, is_active=True))
                created += 1
        db.commit()
        print(f"Product catalogue ready. created={created} updated={updated}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
