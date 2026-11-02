"""Delete a campaign and all dependent workflow / shortlist rows."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import (
    ApprovalDecision,
    AuditEvent,
    Campaign,
    CampaignCustomer,
    ComplianceCheck,
    CustomerScore,
    EligibilityCheck,
    MessageDraft,
    ProductRecommendation,
    SimulatedMessage,
    WorkflowRun,
    WorkflowStep,
)


def delete_campaign_cascade(db: Session, campaign_id: str) -> bool:
    """Remove campaign and related records. Returns False if campaign missing."""
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        return False

    run_ids = list(
        db.scalars(select(WorkflowRun.id).where(WorkflowRun.campaign_id == campaign_id)).all()
    )
    message_ids = list(
        db.scalars(select(MessageDraft.id).where(MessageDraft.campaign_id == campaign_id)).all()
    )

    if message_ids:
        db.execute(delete(SimulatedMessage).where(SimulatedMessage.message_id.in_(message_ids)))
        db.execute(delete(ApprovalDecision).where(ApprovalDecision.message_id.in_(message_ids)))

    db.execute(delete(SimulatedMessage).where(SimulatedMessage.campaign_id == campaign_id))
    db.execute(delete(ApprovalDecision).where(ApprovalDecision.campaign_id == campaign_id))
    db.execute(delete(MessageDraft).where(MessageDraft.campaign_id == campaign_id))
    db.execute(delete(ComplianceCheck).where(ComplianceCheck.campaign_id == campaign_id))
    db.execute(delete(EligibilityCheck).where(EligibilityCheck.campaign_id == campaign_id))
    db.execute(
        delete(ProductRecommendation).where(ProductRecommendation.campaign_id == campaign_id)
    )
    db.execute(delete(CustomerScore).where(CustomerScore.campaign_id == campaign_id))
    db.execute(delete(CampaignCustomer).where(CampaignCustomer.campaign_id == campaign_id))

    if run_ids:
        db.execute(delete(WorkflowStep).where(WorkflowStep.workflow_run_id.in_(run_ids)))
    db.execute(delete(WorkflowRun).where(WorkflowRun.campaign_id == campaign_id))

    db.execute(delete(AuditEvent).where(AuditEvent.campaign_id == campaign_id))
    if run_ids:
        db.execute(delete(AuditEvent).where(AuditEvent.workflow_run_id.in_(run_ids)))

    db.delete(campaign)
    return True
