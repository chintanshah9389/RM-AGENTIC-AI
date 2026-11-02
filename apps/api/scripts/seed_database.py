"""Deterministic synthetic data seeder for Agentic AI Banking CRM POC."""

from __future__ import annotations

import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, func, select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import (
    Account,
    CampaignHistory,
    Customer,
    CustomerConsent,
    Product,
    Transaction,
    User,
)

FIRST_NAMES = [
    "Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Neha", "Arjun", "Isha",
    "Kabir", "Meera", "Aditya", "Sneha", "Rahul", "Pooja", "Siddharth", "Kavya",
    "Nikhil", "Divya", "Aman", "Riya", "Harsh", "Shreya", "Manish", "Tanvi",
    "Yash", "Nisha", "Kunal", "Anjali", "Dev", "Sonal",
]
LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Reddy", "Iyer", "Nair", "Gupta", "Mehta",
    "Joshi", "Khan", "Desai", "Chopra", "Malhotra", "Banerjee", "Pillai",
]
CITIES = [
    "Mumbai", "Pune", "Delhi", "Bengaluru", "Hyderabad",
    "Chennai", "Ahmedabad", "Kolkata",
]
OCCUPATIONS = [
    "Software Engineer", "Bank Manager", "Teacher", "Doctor", "Business Owner",
    "Consultant", "Accountant", "Sales Manager", "Architect", "Analyst",
]
SEGMENTS = ["STANDARD", "GOLD", "PREMIUM", "PRIVATE"]
RISKS = ["LOW", "MEDIUM", "HIGH"]
ACCOUNT_TYPES = ["SAVINGS", "SALARY", "CURRENT", "LOAN", "CREDIT_CARD"]
TXN_CATEGORIES = [
    "SALARY", "SHOPPING", "TRAVEL", "DINING", "UTILITY", "EMI",
    "TRANSFER", "INVESTMENT", "INSURANCE", "HEALTHCARE", "EDUCATION",
]


def _mask_account(rng: random.Random) -> str:
    return f"XXXXXX{rng.randint(1000, 9999)}"


def _write_json(path: Path, payload: list | dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def seed() -> None:
    settings = get_settings()
    rng = random.Random(settings.data_seed)
    data_dir = ROOT.parents[1] / "data"

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        users = [
            User(
                email="rm@demo.bank",
                full_name="Demo Relationship Manager",
                role="RELATIONSHIP_MANAGER",
                password_hash=hash_password("Demo@123"),
            ),
            User(
                email="supervisor@demo.bank",
                full_name="Demo Supervisor",
                role="SUPERVISOR",
                password_hash=hash_password("Demo@123"),
            ),
            User(
                email="admin@demo.bank",
                full_name="Demo Admin",
                role="ADMIN",
                password_hash=hash_password("Demo@123"),
            ),
        ]
        db.add_all(users)

        products = [
            Product(
                product_code="PL_STANDARD",
                name="Personal Loan Standard",
                category="PERSONAL_LOAN",
                min_monthly_income=30000,
                min_customer_value_score=None,
                requires_salary_account=False,
                amount_min=50000,
                amount_max=500000,
                interest_rate=12.50,
                tenure_min_months=12,
                tenure_max_months=48,
                max_risk_category="MEDIUM",
            ),
            Product(
                product_code="PL_PREMIUM",
                name="Personal Loan Premium",
                category="PERSONAL_LOAN",
                min_monthly_income=75000,
                min_customer_value_score=70,
                requires_salary_account=False,
                amount_min=200000,
                amount_max=1500000,
                interest_rate=10.75,
                tenure_min_months=12,
                tenure_max_months=60,
                max_risk_category="MEDIUM",
            ),
            Product(
                product_code="PL_SALARY",
                name="Salary Advantage Loan",
                category="PERSONAL_LOAN",
                min_monthly_income=40000,
                min_customer_value_score=None,
                requires_salary_account=True,
                min_salary_amount=40000,
                amount_min=100000,
                amount_max=800000,
                interest_rate=11.25,
                tenure_min_months=12,
                tenure_max_months=48,
                max_risk_category="MEDIUM",
            ),
            Product(
                product_code="HL_STANDARD",
                name="Home Loan Standard",
                category="HOME_LOAN",
                min_monthly_income=50000,
                min_customer_value_score=60,
                requires_salary_account=False,
                amount_min=1000000,
                amount_max=10000000,
                interest_rate=8.75,
                tenure_min_months=60,
                tenure_max_months=300,
                max_risk_category="MEDIUM",
            ),
            Product(
                product_code="HL_PREMIUM",
                name="Home Loan Premium",
                category="HOME_LOAN",
                min_monthly_income=100000,
                min_customer_value_score=75,
                requires_salary_account=False,
                amount_min=2500000,
                amount_max=25000000,
                interest_rate=8.25,
                tenure_min_months=60,
                tenure_max_months=360,
                max_risk_category="MEDIUM",
            ),
            Product(
                product_code="CC_STANDARD",
                name="Classic Credit Card",
                category="CREDIT_CARD",
                min_monthly_income=25000,
                min_customer_value_score=None,
                requires_salary_account=False,
                amount_min=25000,
                amount_max=200000,
                interest_rate=36.0,
                tenure_min_months=1,
                tenure_max_months=12,
                max_risk_category="MEDIUM",
            ),
        ]
        db.add_all(products)
        db.flush()

        customers: list[Customer] = []
        accounts: list[Account] = []
        transactions: list[Transaction] = []
        consents: list[CustomerConsent] = []
        history: list[CampaignHistory] = []

        # Planted scenarios first (A-F)
        planted = [
            {
                "tag": "A",
                "name": "Priya Sharma",
                "city": "Mumbai",
                "income": 95000,
                "segment": "PREMIUM",
                "risk": "LOW",
                "salary": True,
                "engagement": 88,
                "marketing": True,
                "whatsapp": True,
                "dnc": False,
                "contacts": 0,
                "max_contacts": 3,
                "data_quality": "COMPLETE",
                "products": ["SAVINGS", "SALARY", "CREDIT_CARD"],
            },
            {
                "tag": "B",
                "name": "Rohan Patel",
                "city": "Pune",
                "income": 120000,
                "segment": "PRIVATE",
                "risk": "LOW",
                "salary": True,
                "engagement": 90,
                "marketing": True,
                "whatsapp": True,
                "dnc": True,
                "contacts": 0,
                "max_contacts": 3,
                "data_quality": "COMPLETE",
                "products": ["SAVINGS", "SALARY", "INVESTMENT"],
            },
            {
                "tag": "C",
                "name": "Aman Reddy",
                "city": "Hyderabad",
                "income": 55000,
                "segment": "GOLD",
                "risk": "LOW",
                "salary": False,
                "engagement": 75,
                "marketing": True,
                "whatsapp": True,
                "dnc": False,
                "contacts": 1,
                "max_contacts": 3,
                "data_quality": "COMPLETE",
                "products": ["SAVINGS"],
            },
            {
                "tag": "D",
                "name": "Neha Iyer",
                "city": "Chennai",
                "income": 85000,
                "segment": "PREMIUM",
                "risk": "LOW",
                "salary": True,
                "engagement": 82,
                "marketing": True,
                "whatsapp": True,
                "dnc": False,
                "contacts": 3,
                "max_contacts": 3,
                "data_quality": "COMPLETE",
                "products": ["SAVINGS", "SALARY"],
            },
            {
                "tag": "E",
                "name": "Kabir Singh",
                "city": "Delhi",
                "income": 78000,
                "segment": "GOLD",
                "risk": "MEDIUM",
                "salary": True,
                "engagement": 60,
                "marketing": True,
                "whatsapp": True,
                "dnc": False,
                "contacts": 0,
                "max_contacts": 3,
                "data_quality": "INCOMPLETE_TXN",
                "products": ["SALARY"],
            },
            {
                "tag": "F",
                "name": "Meera Nair",
                "city": "Bengaluru",
                "income": 88000,
                "segment": "PREMIUM",
                "risk": "LOW",
                "salary": True,
                "engagement": 85,
                "marketing": True,
                "whatsapp": False,
                "dnc": False,
                "contacts": 0,
                "max_contacts": 3,
                "data_quality": "COMPLETE",
                "products": ["SAVINGS", "SALARY", "CREDIT_CARD"],
            },
        ]

        today = date.today()

        def add_customer(spec: dict, idx: int, light: bool = False) -> Customer:
            rel_years = rng.randint(2, 12) if spec["tag"] in {"A", "B", "F"} else rng.randint(1, 8)
            customer = Customer(
                customer_code=f"CUST{1000 + idx}",
                full_name=spec["name"],
                age=rng.randint(28, 55),
                city=spec["city"],
                occupation=rng.choice(OCCUPATIONS),
                monthly_income=float(spec["income"]),
                relationship_start_date=today - timedelta(days=365 * rel_years + rng.randint(0, 200)),
                customer_segment=spec["segment"],
                risk_category=spec["risk"],
                is_active=True,
                preferred_language="English",
                preferred_channel="WHATSAPP",
                digital_engagement_score=float(spec["engagement"]),
                has_salary_account=spec["salary"],
                existing_products=spec["products"],
                last_contact_date=today - timedelta(days=rng.randint(10, 90)),
                campaign_response_history=[
                    {"campaign": "PL_Q1", "response": "INTERESTED"},
                    {"campaign": "CC_OFFER", "response": "NO_RESPONSE"},
                ],
                data_quality_flag=spec["data_quality"],
                scenario_tag=spec["tag"] if spec["tag"] in {"A", "B", "C", "D", "E", "F"} else None,
            )
            db.add(customer)
            db.flush()

            # Accounts
            base_bal = spec["income"] * rng.uniform(1.5, 4.5)
            account_types = ["SAVINGS"]
            if spec["salary"] and not light:
                account_types.append("SALARY")
            elif spec["salary"] and light:
                account_types = ["SALARY"]
            for atype in account_types:
                acc = Account(
                    customer_id=customer.id,
                    account_type=atype,
                    masked_account_number=_mask_account(rng),
                    current_balance=round(base_bal * rng.uniform(0.8, 1.2), 2),
                    average_monthly_balance=round(base_bal, 2),
                    status="ACTIVE",
                    opened_date=customer.relationship_start_date,
                    delinquency_days=0 if spec["risk"] == "LOW" else rng.randint(0, 15),
                )
                db.add(acc)
                accounts.append(acc)
            db.flush()

            cust_accounts = [a for a in accounts if a.customer_id == customer.id]
            if spec["data_quality"] == "INCOMPLETE_TXN":
                txn_count = 2
            elif light:
                txn_count = 3
            else:
                txn_count = rng.randint(8, 14)
            for t in range(txn_count):
                acc = rng.choice(cust_accounts)
                category = "SALARY" if t == 0 and spec["salary"] else rng.choice(TXN_CATEGORIES)
                txn_type = "CREDIT" if category == "SALARY" else rng.choice(["CREDIT", "DEBIT"])
                amount = (
                    float(spec["income"])
                    if category == "SALARY"
                    else round(rng.uniform(500, 45000), 2)
                )
                transactions.append(
                    Transaction(
                        customer_id=customer.id,
                        account_id=acc.id,
                        transaction_date=today - timedelta(days=rng.randint(1, 120)),
                        amount=amount,
                        transaction_type=txn_type,
                        transaction_category=category,
                        channel=rng.choice(["MOBILE", "NETBANKING", "UPI", "BRANCH"]),
                        merchant_category=category,
                    )
                )

            consents.append(
                CustomerConsent(
                    customer_id=customer.id,
                    marketing_consent=spec["marketing"],
                    whatsapp_consent=spec["whatsapp"],
                    do_not_contact=spec["dnc"],
                    consent_updated_at=datetime.utcnow() - timedelta(days=rng.randint(5, 60)),
                    maximum_contacts_per_month=spec["max_contacts"],
                    contacts_this_month=spec["contacts"],
                )
            )

            history.append(
                CampaignHistory(
                    customer_id=customer.id,
                    campaign_name="Personal Loan Soft Offer",
                    product_category="PERSONAL_LOAN",
                    channel="WHATSAPP",
                    response=rng.choice(["INTERESTED", "NO_RESPONSE", "OPTED_OUT"]),
                    contacted_at=today - timedelta(days=rng.randint(30, 180)),
                )
            )
            return customer

        for i, spec in enumerate(planted, start=1):
            customers.append(add_customer(spec, i))

        # Scale to 5000 synthetic customers for demo volume.
        target_customers = int(getattr(settings, "customer_seed_count", 5000) or 5000)
        target_customers = max(target_customers, len(planted))
        print(f"Seeding customers 7..{target_customers} (target={target_customers})...")

        for i in range(7, target_customers + 1):
            fname = rng.choice(FIRST_NAMES)
            lname = rng.choice(LAST_NAMES)
            income = rng.choice([28000, 35000, 45000, 60000, 75000, 90000, 110000, 150000])
            segment = (
                "PRIVATE" if income >= 120000 else
                "PREMIUM" if income >= 75000 else
                "GOLD" if income >= 45000 else
                "STANDARD"
            )
            salary = income >= 40000 and rng.random() > 0.3
            # Lighter history for bulk rows to keep seed fast while still detailed enough.
            light = i > 200
            spec = {
                "tag": "X",
                "name": f"{fname} {lname} {i}",
                "city": rng.choice(CITIES),
                "income": income,
                "segment": segment,
                "risk": rng.choices(RISKS, weights=[0.55, 0.35, 0.10])[0],
                "salary": salary,
                "engagement": rng.randint(35, 95),
                "marketing": rng.random() > 0.15,
                "whatsapp": rng.random() > 0.2,
                "dnc": rng.random() < 0.08,
                "contacts": rng.randint(0, 2),
                "max_contacts": 3,
                "data_quality": "COMPLETE",
                "products": ["SAVINGS"] + (["SALARY"] if salary else []) + (
                    ["CREDIT_CARD"] if (not light and rng.random() > 0.5) else []
                ),
            }
            c = add_customer(spec, i, light=light)
            if len(customers) < 50:
                customers.append(c)

            if i % 250 == 0:
                db.add_all(transactions)
                db.add_all(consents)
                db.add_all(history)
                db.commit()
                transactions.clear()
                consents.clear()
                history.clear()
                accounts.clear()
                db.expire_all()
                print(f"  committed through customer {i}/{target_customers}")

        db.add_all(transactions)
        db.add_all(consents)
        db.add_all(history)
        db.commit()

        customer_count = db.scalar(select(func.count()).select_from(Customer)) or 0

        # Export compact JSON snapshots (sample only — full DB holds 5000+)
        sample_customers = list(
            db.scalars(select(Customer).order_by(Customer.customer_code).limit(50)).all()
        )
        sample_ids = {c.id for c in sample_customers}
        sample_accounts = list(
            db.scalars(select(Account).where(Account.customer_id.in_(sample_ids))).all()
        )
        _write_json(
            data_dir / "customers.json",
            [
                {
                    "customerId": c.id,
                    "customerCode": c.customer_code,
                    "fullName": c.full_name,
                    "city": c.city,
                    "monthlyIncome": c.monthly_income,
                    "segment": c.customer_segment,
                    "scenarioTag": c.scenario_tag,
                }
                for c in sample_customers
            ]
            + [{"note": f"Sample of 50 / {customer_count} customers in database"}],
        )
        _write_json(
            data_dir / "accounts.json",
            [
                {
                    "accountId": a.id,
                    "customerId": a.customer_id,
                    "accountType": a.account_type,
                    "maskedAccountNumber": a.masked_account_number,
                    "averageMonthlyBalance": a.average_monthly_balance,
                }
                for a in sample_accounts
            ],
        )
        sample_txns = db.scalars(
            select(Transaction).where(Transaction.customer_id.in_(list(sample_ids))).limit(200)
        ).all()
        _write_json(
            data_dir / "transactions.json",
            [
                {
                    "transactionId": t.id,
                    "customerId": t.customer_id,
                    "amount": t.amount,
                    "category": t.transaction_category,
                    "type": t.transaction_type,
                }
                for t in sample_txns
            ],
        )
        _write_json(
            data_dir / "products.json",
            [
                {
                    "productCode": p.product_code,
                    "name": p.name,
                    "interestRate": p.interest_rate,
                    "minIncome": p.min_monthly_income,
                }
                for p in products
            ],
        )
        sample_consents = db.scalars(
            select(CustomerConsent).where(CustomerConsent.customer_id.in_(list(sample_ids)))
        ).all()
        _write_json(
            data_dir / "consents.json",
            [
                {
                    "customerId": c.customer_id,
                    "marketingConsent": c.marketing_consent,
                    "whatsappConsent": c.whatsapp_consent,
                    "doNotContact": c.do_not_contact,
                    "contactsThisMonth": c.contacts_this_month,
                }
                for c in sample_consents
            ],
        )
        sample_history = db.scalars(
            select(CampaignHistory).where(CampaignHistory.customer_id.in_(list(sample_ids)))
        ).all()
        _write_json(
            data_dir / "campaign-history.json",
            [
                {
                    "customerId": h.customer_id,
                    "campaignName": h.campaign_name,
                    "response": h.response,
                }
                for h in sample_history
            ],
        )

        account_count = db.scalar(select(func.count()).select_from(Account)) or 0
        txn_count = db.scalar(select(func.count()).select_from(Transaction)) or 0
        consent_count = db.scalar(select(func.count()).select_from(CustomerConsent)) or 0

        print("Seed completed successfully.")
        print(f"Users: {len(users)}")
        print(f"Customers: {customer_count}")
        print(f"Accounts: {account_count}")
        print(f"Transactions: {txn_count}")
        print(f"Products: {len(products)}")
        print(f"Consents: {consent_count}")
        print(f"DATA_SEED={settings.data_seed}")
        print("Demo logins: rm@demo.bank / supervisor@demo.bank / admin@demo.bank  password=Demo@123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
