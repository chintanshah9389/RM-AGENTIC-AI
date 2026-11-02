from typing import Any, Optional

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    natural_language_request: str = Field(min_length=10)
    # AUTO = resolved later by Intent agent + product catalogue tools
    product_category: str = "AUTO"
    channel: str = "AUTO"
    max_customers: int = Field(default=10, ge=1, le=50)
    min_value_score: float = Field(default=70, ge=0, le=100)
    min_propensity_score: float = Field(default=60, ge=0, le=100)


class CampaignOut(BaseModel):
    id: str
    name: str
    natural_language_request: str
    product_category: str
    channel: str
    max_customers: int
    min_value_score: float
    min_propensity_score: float
    status: str
    parsed_intent: Optional[dict[str, Any]] = None
    created_at: str

    class Config:
        from_attributes = True


class MessageUpdate(BaseModel):
    body: str = Field(min_length=20)


class DecisionRequest(BaseModel):
    reason: Optional[str] = None
