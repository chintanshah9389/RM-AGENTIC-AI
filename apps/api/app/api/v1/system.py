from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.config import get_settings
from app.core.response import ok
from app.db.session import get_db
from app.models import Product, User

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    settings = get_settings()
    db_url = settings.database_url
    db_engine = "postgres" if db_url.startswith("postgresql") else "sqlite"
    return ok(
        {
            "status": "ok",
            "app": settings.app_name,
            "env": settings.app_env,
            "llmProvider": settings.llm_provider,
            "messagingProvider": settings.messaging_provider,
            "orchestratorEngine": settings.orchestrator_engine,
            "databaseEngine": db_engine,
            "framework": {
                "langgraph": True,
                "langchain": True,
                "langchainCore": True,
                "langchainAgents": True,
                "langchainTools": True,
                "agentPattern": (
                    "LangGraph orchestrates; Intent/Retrieval/Message use "
                    "langchain.agents.create_agent + tools; "
                    "Value/Eligibility/Compliance stay deterministic"
                ),
            },
        }
    )


@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return ok({"status": "ready"})


@router.get("/admin/products")
def admin_products(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN", "SUPERVISOR", "RELATIONSHIP_MANAGER")),
):
    products = db.scalars(select(Product)).all()
    return ok(
        [
            {
                "id": p.id,
                "code": p.product_code,
                "name": p.name,
                "minIncome": p.min_monthly_income,
                "rate": p.interest_rate,
                "disclaimer": p.disclaimer,
            }
            for p in products
        ]
    )


@router.get("/admin/rules")
def admin_rules(user: User = Depends(get_current_user)):
    settings = get_settings()
    return ok(
        {
            "eligibilityRules": [
                "CUSTOMER_ACTIVE",
                "AGE_ALLOWED",
                "MINIMUM_INCOME",
                "MAXIMUM_RISK_LEVEL",
                "NO_SEVERE_DELINQUENCY",
                "SALARY_ACCOUNT_REQUIRED",
                "MINIMUM_CUSTOMER_VALUE",
            ],
            "complianceRules": [
                "MARKETING_CONSENT",
                "WHATSAPP_CONSENT",
                "DO_NOT_CONTACT",
                "CONTACT_FREQUENCY_LIMIT",
            ],
            "scoring": {
                "valueWeights": {
                    "AMB": 0.30,
                    "salaryConsistency": 0.20,
                    "tenure": 0.15,
                    "productHoldings": 0.15,
                    "transactionActivity": 0.10,
                    "digitalEngagement": 0.10,
                },
                "notice": "Demonstration heuristic scores only.",
            },
            "llmProvider": settings.llm_provider,
            "messagingProvider": settings.messaging_provider,
            "dataSeed": settings.data_seed,
        }
    )
