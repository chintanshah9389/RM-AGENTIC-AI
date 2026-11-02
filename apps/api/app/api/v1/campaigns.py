from __future__ import annotations

import logging
import threading
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.response import ok
from app.db.session import SessionLocal, get_db
from app.models import (
    Account,
    ApprovalDecision,
    Campaign,
    CampaignCustomer,
    ComplianceCheck,
    Customer,
    CustomerScore,
    EligibilityCheck,
    MessageDraft,
    Product,
    ProductRecommendation,
    User,
    WorkflowRun,
)
from app.schemas.campaign import CampaignCreate, DecisionRequest, MessageUpdate
from app.services.activity_log import build_activity_lines, sanitize_step_details
from app.services.audit import write_audit
from app.services.campaign_cleanup import delete_campaign_cascade
from app.services.messaging import get_messaging_provider
from app.workflows.orchestrator import SupervisorOrchestrator

logger = logging.getLogger(__name__)


def _run_workflow_in_background(run_id: str, user_id: str, user_role: str) -> None:
    db = SessionLocal()
    try:
        SupervisorOrchestrator(db).execute_campaign_run(
            run_id, user_id=user_id, user_role=user_role
        )
    except Exception:  # noqa: BLE001
        logger.exception("Background workflow failed for run %s", run_id)
    finally:
        db.close()

router = APIRouter(tags=["campaigns"])


@router.post("/campaigns")
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("RELATIONSHIP_MANAGER", "SUPERVISOR", "ADMIN")),
):
    campaign = Campaign(
        name=payload.name,
        natural_language_request=payload.natural_language_request,
        product_category=payload.product_category,
        channel=payload.channel,
        max_customers=payload.max_customers,
        min_value_score=payload.min_value_score,
        min_propensity_score=payload.min_propensity_score,
        status="DRAFT",
        created_by=user.id,
    )
    db.add(campaign)
    db.flush()
    write_audit(
        db,
        event_type="CAMPAIGN_CREATED",
        summary=f"Campaign created: {campaign.name}",
        user_id=user.id,
        user_role=user.role,
        campaign_id=campaign.id,
    )
    db.commit()
    db.refresh(campaign)
    return ok(_campaign_dict(campaign))


@router.get("/campaigns")
def list_campaigns(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = db.scalars(select(Campaign).order_by(Campaign.created_at.desc())).all()
    return ok([_campaign_dict(c) for c in rows])


@router.get("/campaigns/{campaign_id}")
def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return ok(_campaign_dict(campaign))


@router.delete("/campaigns/{campaign_id}")
def delete_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("RELATIONSHIP_MANAGER", "SUPERVISOR", "ADMIN")),
):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    name = campaign.name
    deleted = delete_campaign_cascade(db, campaign_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Campaign not found")

    write_audit(
        db,
        event_type="CAMPAIGN_DELETED",
        summary=f"Campaign deleted: {name}",
        status="SUCCESS",
        user_id=user.id,
        user_role=user.role,
    )
    db.commit()
    return ok({"id": campaign_id, "deleted": True, "name": name})


@router.post("/campaigns/{campaign_id}/run")
def run_campaign(
    campaign_id: str,
    wait: bool = Query(
        default=False,
        description="If true, block until agents finish. Default starts in background for live UI.",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("RELATIONSHIP_MANAGER", "ADMIN")),
):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    orchestrator = SupervisorOrchestrator(db)
    if wait:
        run = orchestrator.run_campaign(campaign, user_id=user.id, user_role=user.role)
    else:
        run = orchestrator.bootstrap_campaign_run(
            campaign, user_id=user.id, user_role=user.role
        )
        thread = threading.Thread(
            target=_run_workflow_in_background,
            args=(run.id, user.id, user.role),
            daemon=True,
            name=f"workflow-{run.id[:8]}",
        )
        thread.start()

    db.refresh(campaign)
    return ok(
        {
            "campaign": _campaign_dict(campaign),
            "workflow": {
                "id": run.id,
                "status": run.workflow_status,
                "correlationId": run.correlation_id,
                "currentStep": run.current_step,
                "async": not wait,
            },
        }
    )


@router.get("/campaigns/{campaign_id}/results")
def campaign_results(
    campaign_id: str,
    search: str | None = None,
    propensity: str | None = None,
    compliance: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    rows = db.scalars(
        select(CampaignCustomer)
        .where(CampaignCustomer.campaign_id == campaign_id)
        .order_by(CampaignCustomer.rank.asc())
    ).all()

    results = []
    for row in rows:
        customer = db.get(Customer, row.customer_id)
        product = db.get(Product, row.recommended_product_id) if row.recommended_product_id else None
        message = db.scalar(
            select(MessageDraft).where(
                MessageDraft.campaign_id == campaign_id,
                MessageDraft.customer_id == row.customer_id,
            )
        )
        if search and customer and search.lower() not in customer.full_name.lower():
            continue
        if propensity and row.propensity_score is not None:
            cls = _class(row.propensity_score)
            if cls != propensity.upper():
                continue
        if compliance and (row.compliance_status or "").upper() != compliance.upper():
            continue

        results.append(
            {
                "campaignCustomerId": row.id,
                "rank": row.rank,
                "customerId": row.customer_id,
                "customerName": customer.full_name if customer else None,
                "segment": customer.customer_segment if customer else None,
                "city": customer.city if customer else None,
                "monthlyIncome": customer.monthly_income if customer else None,
                "valueScore": row.value_score,
                "propensityScore": row.propensity_score,
                "recommendedProduct": product.name if product else None,
                "eligibility": row.eligibility_status,
                "compliance": row.compliance_status,
                "contactAllowed": row.contact_allowed,
                "messageStatus": message.status if message else None,
                "messageId": message.id if message else None,
                "explanation": row.explanation,
                "scenarioTag": customer.scenario_tag if customer else None,
            }
        )

    intent = campaign.parsed_intent or {}
    product_resolved = bool(intent.get("productCategoryResolved", True)) if intent else True
    no_data_message = None
    if intent and not intent.get("productCategoryResolved"):
        no_data_message = intent.get("productUnavailableMessage") or (
            "No data found. The requested product is not in the catalogue/database."
        )
    elif len(results) == 0:
        no_data_message = "No data found. No matching customers for this campaign."

    return ok(
        {
            "campaignId": campaign_id,
            "count": len(results),
            "disclaimer": "POC Environment - Synthetic Data",
            "results": results,
            "productCategory": campaign.product_category,
            "requestedProductCategory": intent.get("requestedProductCategory"),
            "productCategoryResolved": product_resolved if intent else None,
            "availableProductCategories": intent.get("availableProductCategories") or [],
            "noData": len(results) == 0,
            "noDataMessage": no_data_message,
        }
    )


@router.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    run = db.get(WorkflowRun, workflow_id)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return ok(
        {
            "id": run.id,
            "campaignId": run.campaign_id,
            "correlationId": run.correlation_id,
            "status": run.workflow_status,
            "currentStep": run.current_step,
            "completedSteps": run.completed_steps,
            "startedAt": run.started_at.isoformat() if run.started_at else None,
            "completedAt": run.completed_at.isoformat() if run.completed_at else None,
            "stateSnapshot": run.state_snapshot,
        }
    )


@router.get("/workflows/{workflow_id}/steps")
def get_workflow_steps(
    workflow_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = db.get(WorkflowRun, workflow_id)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow not found")
    steps = sorted(run.steps, key=lambda s: s.step_order)
    payload = []
    for s in steps:
        details = sanitize_step_details(s.details if isinstance(s.details, dict) else {})
        activity = build_activity_lines(
            agent_name=s.agent_name,
            status=s.status,
            summary=s.summary,
            details=details,
            processed_records=s.processed_records or 0,
            duration_ms=s.duration_ms,
        )
        payload.append(
            {
                "id": s.id,
                "agentName": s.agent_name,
                "stepOrder": s.step_order,
                "status": s.status,
                "summary": s.summary,
                "processedRecords": s.processed_records,
                "startedAt": s.started_at.isoformat() if s.started_at else None,
                "completedAt": s.completed_at.isoformat() if s.completed_at else None,
                "durationMs": s.duration_ms,
                "error": s.error,
                "details": details,
                "activity": activity,
            }
        )
    return ok(payload)


@router.get("/customers")
def list_customers(
    search: str | None = None,
    segment: str | None = None,
    city: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Customer).where(Customer.is_active.is_(True))
    count_stmt = select(func.count()).select_from(Customer).where(Customer.is_active.is_(True))

    if search:
        like = f"%{search}%"
        filt = or_(Customer.full_name.ilike(like), Customer.customer_code.ilike(like))
        stmt = stmt.where(filt)
        count_stmt = count_stmt.where(filt)
    if segment:
        stmt = stmt.where(Customer.customer_segment == segment.upper())
        count_stmt = count_stmt.where(Customer.customer_segment == segment.upper())
    if city:
        stmt = stmt.where(Customer.city == city)
        count_stmt = count_stmt.where(Customer.city == city)

    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(Customer.monthly_income.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    customer_ids = [c.id for c in rows]
    accounts_by_customer: dict[str, list[dict]] = {cid: [] for cid in customer_ids}
    if customer_ids:
        account_rows = db.scalars(
            select(Account)
            .where(Account.customer_id.in_(customer_ids))
            .order_by(Account.account_type.asc())
        ).all()
        for acc in account_rows:
            accounts_by_customer.setdefault(acc.customer_id, []).append(
                {
                    "accountType": acc.account_type,
                    "maskedAccountNumber": acc.masked_account_number,
                    "status": acc.status,
                }
            )

    items = []
    for c in rows:
        accounts = accounts_by_customer.get(c.id) or []
        primary = accounts[0] if accounts else None
        items.append(
            {
                "customerId": c.id,
                "customerCode": c.customer_code,
                "fullName": c.full_name,
                "age": c.age,
                "city": c.city,
                "occupation": c.occupation,
                "segment": c.customer_segment,
                "monthlyIncome": c.monthly_income,
                "riskCategory": c.risk_category,
                "scenarioTag": c.scenario_tag,
                "hasSalaryAccount": c.has_salary_account,
                "accountType": primary["accountType"] if primary else None,
                "maskedAccountNumber": primary["maskedAccountNumber"] if primary else None,
                "accounts": accounts,
                "accountCount": len(accounts),
            }
        )

    return ok(
        {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "totalPages": max(1, (total + page_size - 1) // page_size),
            "items": items,
            "disclaimer": "POC Environment - Synthetic Data",
        }
    )


@router.get("/customers/{customer_id}")
def get_customer(
    customer_id: str,
    campaign_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.tools.customer_tools import get_customer_360_by_id

    profile = get_customer_360_by_id(db, customer_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Customer not found")

    payload: dict = {"profile": profile, "campaignContext": None}
    if campaign_id:
        payload["campaignContext"] = _customer_campaign_context(db, campaign_id, customer_id)
    return ok(payload)


@router.get("/customers/{customer_id}/recommendation")
def get_recommendation(
    customer_id: str,
    campaign_id: str = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return ok(_customer_campaign_context(db, campaign_id, customer_id))


@router.get("/campaigns/{campaign_id}/messages")
def list_messages(
    campaign_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    messages = db.scalars(
        select(MessageDraft).where(MessageDraft.campaign_id == campaign_id)
    ).all()
    return ok(
        [
            {
                "id": m.id,
                "campaignId": m.campaign_id,
                "customerId": m.customer_id,
                "body": m.body,
                "status": m.status,
                "channel": m.channel,
                "llmProviderUsed": m.llm_provider_used,
            }
            for m in messages
        ]
    )


@router.patch("/messages/{message_id}")
def update_message(
    message_id: str,
    payload: MessageUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("RELATIONSHIP_MANAGER", "ADMIN")),
):
    message = db.get(MessageDraft, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.status in {"SIMULATED_SENT"}:
        raise HTTPException(status_code=400, detail="Sent messages cannot be edited")
    if not _contact_allowed(db, message.campaign_id, message.customer_id):
        raise HTTPException(status_code=400, detail="Blocked customers cannot have message edits for send")

    message.body = payload.body
    message.updated_at = datetime.utcnow()
    if message.status == "APPROVED":
        message.status = "DRAFT"
    db.commit()
    db.refresh(message)
    return ok(_message_dict(message))


@router.post("/messages/{message_id}/approve")
def approve_message(
    message_id: str,
    payload: DecisionRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("RELATIONSHIP_MANAGER", "ADMIN")),
):
    message = db.get(MessageDraft, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if not _contact_allowed(db, message.campaign_id, message.customer_id):
        raise HTTPException(status_code=400, detail="Compliance blocked. Approval not allowed.")

    message.status = "APPROVED"
    message.updated_at = datetime.utcnow()
    db.add(
        ApprovalDecision(
            message_id=message.id,
            campaign_id=message.campaign_id,
            customer_id=message.customer_id,
            decision="APPROVED",
            decided_by=user.id,
            reason=(payload.reason if payload else None),
        )
    )
    write_audit(
        db,
        event_type="MESSAGE_APPROVED",
        summary="RM approved WhatsApp draft",
        status="SUCCESS",
        user_id=user.id,
        user_role=user.role,
        campaign_id=message.campaign_id,
        customer_id=message.customer_id,
    )
    db.commit()
    return ok(_message_dict(message))


@router.post("/messages/{message_id}/reject")
def reject_message(
    message_id: str,
    payload: DecisionRequest | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("RELATIONSHIP_MANAGER", "ADMIN")),
):
    message = db.get(MessageDraft, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    message.status = "REJECTED"
    message.updated_at = datetime.utcnow()
    db.add(
        ApprovalDecision(
            message_id=message.id,
            campaign_id=message.campaign_id,
            customer_id=message.customer_id,
            decision="REJECTED",
            decided_by=user.id,
            reason=(payload.reason if payload else None),
        )
    )
    write_audit(
        db,
        event_type="MESSAGE_REJECTED",
        summary="RM rejected WhatsApp draft",
        status="SUCCESS",
        user_id=user.id,
        user_role=user.role,
        campaign_id=message.campaign_id,
        customer_id=message.customer_id,
    )
    db.commit()
    return ok(_message_dict(message))


@router.post("/messages/{message_id}/simulate-send")
def simulate_send(
    message_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("RELATIONSHIP_MANAGER", "ADMIN")),
):
    message = db.get(MessageDraft, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    allowed = _contact_allowed(db, message.campaign_id, message.customer_id)
    provider = get_messaging_provider()
    try:
        result = provider.send_message(
            db,
            message=message,
            contact_allowed=allowed,
            user_id=user.id,
            user_role=user.role,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return ok(result)


@router.get("/audit-events")
def list_audit(
    campaign_id: str | None = None,
    workflow_run_id: str | None = None,
    limit: int = Query(default=100, le=300),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models import AuditEvent

    stmt = select(AuditEvent)
    if workflow_run_id:
        stmt = stmt.where(AuditEvent.workflow_run_id == workflow_run_id)
    elif campaign_id:
        stmt = stmt.where(AuditEvent.campaign_id == campaign_id)
    stmt = stmt.order_by(AuditEvent.timestamp.asc()).limit(limit)
    events = db.scalars(stmt).all()
    return ok(
        [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "userId": e.user_id,
                "userRole": e.user_role,
                "campaignId": e.campaign_id,
                "workflowRunId": e.workflow_run_id,
                "customerId": e.customer_id,
                "agentName": e.agent_name,
                "eventType": e.event_type,
                "status": e.status,
                "summary": e.summary,
                "correlationId": e.correlation_id,
                "metadata": e.metadata_json or {},
            }
            for e in events
        ]
    )


def _campaign_dict(campaign: Campaign) -> dict:
    return {
        "id": campaign.id,
        "name": campaign.name,
        "naturalLanguageRequest": campaign.natural_language_request,
        "productCategory": campaign.product_category,
        "channel": campaign.channel,
        "maxCustomers": campaign.max_customers,
        "minValueScore": campaign.min_value_score,
        "minPropensityScore": campaign.min_propensity_score,
        "status": campaign.status,
        "parsedIntent": campaign.parsed_intent,
        "createdAt": campaign.created_at.isoformat() if campaign.created_at else None,
    }


def _message_dict(message: MessageDraft) -> dict:
    return {
        "id": message.id,
        "campaignId": message.campaign_id,
        "customerId": message.customer_id,
        "body": message.body,
        "status": message.status,
        "channel": message.channel,
        "llmProviderUsed": message.llm_provider_used,
    }


def _contact_allowed(db: Session, campaign_id: str, customer_id: str) -> bool:
    check = db.scalar(
        select(ComplianceCheck).where(
            ComplianceCheck.campaign_id == campaign_id,
            ComplianceCheck.customer_id == customer_id,
        )
    )
    return bool(check and check.contact_allowed)


def _class(score: float) -> str:
    if score < 40:
        return "LOW"
    if score < 70:
        return "MEDIUM"
    return "HIGH"


def _customer_campaign_context(db: Session, campaign_id: str, customer_id: str) -> dict:
    value = db.scalar(
        select(CustomerScore).where(
            CustomerScore.campaign_id == campaign_id,
            CustomerScore.customer_id == customer_id,
            CustomerScore.score_type == "VALUE",
        )
    )
    prop = db.scalar(
        select(CustomerScore).where(
            CustomerScore.campaign_id == campaign_id,
            CustomerScore.customer_id == customer_id,
            CustomerScore.score_type == "PROPENSITY",
        )
    )
    rec = db.scalar(
        select(ProductRecommendation).where(
            ProductRecommendation.campaign_id == campaign_id,
            ProductRecommendation.customer_id == customer_id,
        )
    )
    elig = db.scalar(
        select(EligibilityCheck).where(
            EligibilityCheck.campaign_id == campaign_id,
            EligibilityCheck.customer_id == customer_id,
        )
    )
    comp = db.scalar(
        select(ComplianceCheck).where(
            ComplianceCheck.campaign_id == campaign_id,
            ComplianceCheck.customer_id == customer_id,
        )
    )
    message = db.scalar(
        select(MessageDraft).where(
            MessageDraft.campaign_id == campaign_id,
            MessageDraft.customer_id == customer_id,
        )
    )
    cc = db.scalar(
        select(CampaignCustomer).where(
            CampaignCustomer.campaign_id == campaign_id,
            CampaignCustomer.customer_id == customer_id,
        )
    )
    product = db.get(Product, rec.product_id) if rec else None

    return {
        "campaignId": campaign_id,
        "customerId": customer_id,
        "valueScore": None
        if not value
        else {
            "overallScore": value.overall_score,
            "classification": value.classification,
            "componentScores": value.component_scores,
            "positiveFactors": value.positive_factors,
            "warnings": value.warnings,
            "explanation": value.explanation,
        },
        "propensityScore": None
        if not prop
        else {
            "overallScore": prop.overall_score,
            "classification": prop.classification,
            "componentScores": prop.component_scores,
            "positiveFactors": prop.positive_factors,
            "negativeFactors": prop.negative_factors,
            "warnings": prop.warnings,
            "explanation": prop.explanation,
        },
        "recommendation": None
        if not rec
        else {
            "productId": rec.product_id,
            "productName": product.name if product else None,
            "matchScore": rec.match_score,
            "reason": rec.reason,
            "indicativeAmountMin": rec.indicative_amount_min,
            "indicativeAmountMax": rec.indicative_amount_max,
            "indicativeRate": rec.indicative_rate,
            "tenureMin": rec.tenure_min,
            "tenureMax": rec.tenure_max,
            "conditions": rec.conditions,
            "disclaimer": "Dummy demonstration data. Not a real bank offer.",
        },
        "eligibility": None
        if not elig
        else {"overallPassed": elig.overall_passed, "rules": elig.rules},
        "compliance": None
        if not comp
        else {
            "complianceStatus": comp.compliance_status,
            "contactAllowed": comp.contact_allowed,
            "failedChecks": comp.failed_checks,
            "warnings": comp.warnings,
            "explanation": comp.explanation,
            "details": comp.details,
        },
        "message": None if not message else _message_dict(message),
        "explanation": cc.explanation if cc else None,
        "disclaimer": (
            "Demonstration only. Scores, recommendations and offers do not represent "
            "real lending or credit decisions."
        ),
    }
