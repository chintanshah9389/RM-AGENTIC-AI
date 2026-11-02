from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import ok
from app.db.session import get_db
from app.models import Campaign, ComplianceCheck, Customer, MessageDraft, SimulatedMessage, User, WorkflowRun

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    campaigns = db.scalar(select(func.count()).select_from(Campaign)) or 0
    customers = db.scalar(select(func.count()).select_from(Customer)) or 0
    pending = db.scalar(
        select(func.count()).select_from(MessageDraft).where(MessageDraft.status == "DRAFT")
    ) or 0
    approved = db.scalar(
        select(func.count()).select_from(MessageDraft).where(MessageDraft.status == "APPROVED")
    ) or 0
    blocked = db.scalar(
        select(func.count())
        .select_from(ComplianceCheck)
        .where(ComplianceCheck.contact_allowed.is_(False))
    ) or 0
    sent = db.scalar(select(func.count()).select_from(SimulatedMessage)) or 0

    recent_campaigns = db.scalars(select(Campaign).order_by(Campaign.created_at.desc()).limit(5)).all()
    recent_workflows = db.scalars(
        select(WorkflowRun).order_by(WorkflowRun.started_at.desc()).limit(5)
    ).all()

    return ok(
        {
            "welcome": f"Welcome, {user.full_name}",
            "role": user.role,
            "kpis": {
                "aiCampaigns": campaigns,
                "customersAnalysed": customers,
                "pendingApprovals": pending,
                "approvedMessages": approved,
                "complianceBlocks": blocked,
                "simulatedMessagesSent": sent,
            },
            "recentCampaigns": [
                {
                    "id": c.id,
                    "name": c.name,
                    "status": c.status,
                    "createdAt": c.created_at.isoformat() if c.created_at else None,
                }
                for c in recent_campaigns
            ],
            "recentWorkflows": [
                {
                    "id": w.id,
                    "campaignId": w.campaign_id,
                    "status": w.workflow_status,
                    "currentStep": w.current_step,
                }
                for w in recent_workflows
            ],
            "disclaimer": "POC Environment - Synthetic Data",
        }
    )
