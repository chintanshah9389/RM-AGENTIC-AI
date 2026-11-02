"""Structured outputs for LangChain create_agent response_format."""

from __future__ import annotations

from pydantic import BaseModel, Field


class IntentSchema(BaseModel):
    productCategory: str | None = Field(
        default=None,
        description=(
            "Must match an availableCategories value from list_active_products. "
            "Omit or null when the RM request is not in the catalogue — never substitute another product."
        ),
    )
    customerSegment: str = Field(
        description="HIGH_VALUE | PREMIUM | STANDARD | SALARY_ACCOUNT | PRIVATE | GOLD"
    )
    campaignPeriod: str = Field(default="CURRENT_MONTH")
    channel: str = Field(description="WHATSAPP | EMAIL — follow the RM request")
    maximumCustomers: int = Field(ge=1, le=50, default=10)
    requiresMessageGeneration: bool = True
    minValueScore: float = Field(ge=0, le=100, default=60)
    minPropensityScore: float = Field(ge=0, le=100, default=50)


class RetrievalPlanSchema(BaseModel):
    segmentHint: str = Field(description="Segment filter for search_customers tool")
    minIncome: float = Field(ge=0, default=30000)
    limit: int = Field(ge=1, le=100, default=20)
    notes: str = Field(default="", description="Short retrieval rationale")


class MessageDraftSchema(BaseModel):
    body: str = Field(description="Compliant WhatsApp promotional message body")
