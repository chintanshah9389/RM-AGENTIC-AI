import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    customer_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    age: Mapped[int] = mapped_column(Integer)
    city: Mapped[str] = mapped_column(String(100), index=True)
    occupation: Mapped[str] = mapped_column(String(100))
    monthly_income: Mapped[float] = mapped_column(Float)
    relationship_start_date: Mapped[date] = mapped_column(Date)
    customer_segment: Mapped[str] = mapped_column(String(50), index=True)
    risk_category: Mapped[str] = mapped_column(String(20), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    preferred_language: Mapped[str] = mapped_column(String(50), default="English")
    preferred_channel: Mapped[str] = mapped_column(String(50), default="WHATSAPP")
    digital_engagement_score: Mapped[float] = mapped_column(Float, default=50.0)
    has_salary_account: Mapped[bool] = mapped_column(Boolean, default=False)
    existing_products: Mapped[list] = mapped_column(JSON, default=list)
    last_contact_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    campaign_response_history: Mapped[list] = mapped_column(JSON, default=list)
    data_quality_flag: Mapped[str] = mapped_column(String(50), default="COMPLETE")
    scenario_tag: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    accounts = relationship("Account", back_populates="customer")
    transactions = relationship("Transaction", back_populates="customer")
    consent = relationship("CustomerConsent", back_populates="customer", uselist=False)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    account_type: Mapped[str] = mapped_column(String(50))
    masked_account_number: Mapped[str] = mapped_column(String(32))
    current_balance: Mapped[float] = mapped_column(Float)
    average_monthly_balance: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    opened_date: Mapped[date] = mapped_column(Date)
    delinquency_days: Mapped[int] = mapped_column(Integer, default=0)

    customer = relationship("Customer", back_populates="accounts")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("accounts.id"), index=True)
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    amount: Mapped[float] = mapped_column(Float)
    transaction_type: Mapped[str] = mapped_column(String(20))
    transaction_category: Mapped[str] = mapped_column(String(50))
    channel: Mapped[str] = mapped_column(String(50))
    merchant_category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    customer = relationship("Customer", back_populates="transactions")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    product_code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(50), default="PERSONAL_LOAN")
    min_monthly_income: Mapped[float] = mapped_column(Float)
    min_customer_value_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    requires_salary_account: Mapped[bool] = mapped_column(Boolean, default=False)
    min_salary_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    amount_min: Mapped[float] = mapped_column(Float)
    amount_max: Mapped[float] = mapped_column(Float)
    interest_rate: Mapped[float] = mapped_column(Float)
    tenure_min_months: Mapped[int] = mapped_column(Integer)
    tenure_max_months: Mapped[int] = mapped_column(Integer)
    max_risk_category: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    disclaimer: Mapped[str] = mapped_column(
        Text,
        default="Dummy demonstration data. Not a real bank offer.",
    )


class CustomerConsent(Base):
    __tablename__ = "customer_consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), unique=True, index=True
    )
    marketing_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    whatsapp_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    do_not_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    preferred_contact_start: Mapped[str] = mapped_column(String(10), default="09:00")
    preferred_contact_end: Mapped[str] = mapped_column(String(10), default="20:00")
    maximum_contacts_per_month: Mapped[int] = mapped_column(Integer, default=3)
    contacts_this_month: Mapped[int] = mapped_column(Integer, default=0)

    customer = relationship("Customer", back_populates="consent")


class CampaignHistory(Base):
    __tablename__ = "campaign_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    campaign_name: Mapped[str] = mapped_column(String(255))
    product_category: Mapped[str] = mapped_column(String(50))
    channel: Mapped[str] = mapped_column(String(50))
    response: Mapped[str] = mapped_column(String(50))
    contacted_at: Mapped[date] = mapped_column(Date)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255))
    natural_language_request: Mapped[str] = mapped_column(Text)
    product_category: Mapped[str] = mapped_column(String(50), default="PERSONAL_LOAN")
    channel: Mapped[str] = mapped_column(String(50), default="WHATSAPP")
    max_customers: Mapped[int] = mapped_column(Integer, default=10)
    min_value_score: Mapped[float] = mapped_column(Float, default=70.0)
    min_propensity_score: Mapped[float] = mapped_column(Float, default=60.0)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", index=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    parsed_intent: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    customers = relationship("CampaignCustomer", back_populates="campaign")
    workflow_runs = relationship("WorkflowRun", back_populates="campaign")


class CampaignCustomer(Base):
    __tablename__ = "campaign_customers"
    __table_args__ = (UniqueConstraint("campaign_id", "customer_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    value_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    propensity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_product_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    eligibility_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    compliance_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    campaign = relationship("Campaign", back_populates="customers")


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True)
    correlation_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    original_request: Mapped[str] = mapped_column(Text)
    workflow_status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True)
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    completed_steps: Mapped[list] = mapped_column(JSON, default=list)
    state_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    errors: Mapped[list] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    campaign = relationship("Campaign", back_populates="workflow_runs")
    steps = relationship("WorkflowStep", back_populates="workflow_run")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workflow_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflow_runs.id"), index=True
    )
    agent_name: Mapped[str] = mapped_column(String(100))
    step_order: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processed_records: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    workflow_run = relationship("WorkflowRun", back_populates="steps")


class CustomerScore(Base):
    __tablename__ = "customer_scores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    score_type: Mapped[str] = mapped_column(String(50))
    overall_score: Mapped[float] = mapped_column(Float)
    classification: Mapped[str] = mapped_column(String(20))
    component_scores: Mapped[dict] = mapped_column(JSON, default=dict)
    positive_factors: Mapped[list] = mapped_column(JSON, default=list)
    negative_factors: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ProductRecommendation(Base):
    __tablename__ = "product_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"))
    match_score: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    indicative_amount_min: Mapped[float] = mapped_column(Float)
    indicative_amount_max: Mapped[float] = mapped_column(Float)
    indicative_rate: Mapped[float] = mapped_column(Float)
    tenure_min: Mapped[int] = mapped_column(Integer)
    tenure_max: Mapped[int] = mapped_column(Integer)
    conditions: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class EligibilityCheck(Base):
    __tablename__ = "eligibility_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"))
    overall_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    rules: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    compliance_status: Mapped[str] = mapped_column(String(50))
    contact_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_checks: Mapped[list] = mapped_column(JSON, default=list)
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[str] = mapped_column(Text, default="")
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class MessageDraft(Base):
    __tablename__ = "message_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    channel: Mapped[str] = mapped_column(String(50), default="WHATSAPP")
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="DRAFT", index=True)
    llm_provider_used: Mapped[str] = mapped_column(String(50), default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ApprovalDecision(Base):
    __tablename__ = "approval_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("message_drafts.id"), index=True)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    decision: Mapped[str] = mapped_column(String(50))
    decided_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class SimulatedMessage(Base):
    __tablename__ = "simulated_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("message_drafts.id"), index=True)
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id"), index=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    external_message_id: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="SIMULATED_SENT")
    disclaimer: Mapped[str] = mapped_column(
        Text,
        default="Simulated WhatsApp send. No real customer message was sent.",
    )
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    workflow_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    campaign_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    agent_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(50), default="INFO")
    summary: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
