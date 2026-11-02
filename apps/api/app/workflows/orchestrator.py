from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.agents import (
    ConsentComplianceAgent,
    ConversionPropensityAgent,
    CustomerRetrievalAgent,
    CustomerValueAgent,
    EligibilityAgent,
    ExplainabilityAgent,
    IntentUnderstandingAgent,
    MessageGenerationAgent,
    ProductRecommendationAgent,
)
from app.core.config import get_settings
from app.llm import get_llm_provider
from app.models import (
    Campaign,
    CampaignCustomer,
    ComplianceCheck,
    CustomerScore,
    EligibilityCheck,
    MessageDraft,
    ProductRecommendation,
    WorkflowRun,
    WorkflowStep,
)
from app.services.activity_log import extract_agent_telemetry
from app.services.audit import write_audit
from app.workflows.langgraph_pipeline import build_campaign_graph


AGENT_PIPELINE = [
    "SupervisorOrchestrator",
    "IntentUnderstandingAgent",
    "CustomerRetrievalAgent",
    "CustomerValueAgent",
    "ConversionPropensityAgent",
    "ProductRecommendationAgent",
    "EligibilityAgent",
    "ConsentComplianceAgent",
    "MessageGenerationAgent",
    "ExplainabilityAgent",
    "HumanApproval",
]

LANGGRAPH_AGENT_ORDER = [
    "IntentUnderstandingAgent",
    "CustomerRetrievalAgent",
    "CustomerValueAgent",
    "ConversionPropensityAgent",
    "ProductRecommendationAgent",
    "EligibilityAgent",
    "ConsentComplianceAgent",
    "MessageGenerationAgent",
    "ExplainabilityAgent",
]


class SupervisorOrchestrator:
    """Coordinates specialized agents via LangGraph (architecture default).

    Persistence, ranking, human-approval gating remain in this supervisor layer.
    """

    def __init__(self, db: Session, llm_provider_name: str | None = None) -> None:
        self.db = db
        self.llm = get_llm_provider(llm_provider_name)
        self.settings = get_settings()
        self.engine_name = (self.settings.orchestrator_engine or "langgraph").lower()

    def bootstrap_campaign_run(
        self,
        campaign: Campaign,
        user_id: str,
        user_role: str,
    ) -> WorkflowRun:
        """Create workflow + pending steps and commit so the UI can poll immediately."""
        correlation_id = str(uuid.uuid4())
        run = WorkflowRun(
            campaign_id=campaign.id,
            correlation_id=correlation_id,
            user_id=user_id,
            original_request=campaign.natural_language_request,
            workflow_status="RUNNING",
            current_step="SupervisorOrchestrator",
            completed_steps=[],
            errors=[],
            started_at=datetime.utcnow(),
        )
        self.db.add(run)
        self.db.flush()

        for idx, name in enumerate(AGENT_PIPELINE):
            self.db.add(
                WorkflowStep(
                    workflow_run_id=run.id,
                    agent_name=name,
                    step_order=idx,
                    status="PENDING",
                )
            )
        self.db.flush()

        write_audit(
            self.db,
            event_type="WORKFLOW_STARTED",
            summary=(
                f"Supervisor started multi-agent campaign workflow "
                f"(engine={self.engine_name})"
            ),
            status="INFO",
            user_id=user_id,
            user_role=user_role,
            correlation_id=correlation_id,
            workflow_run_id=run.id,
            campaign_id=campaign.id,
            agent_name="SupervisorOrchestrator",
            metadata={"orchestratorEngine": self.engine_name},
        )

        supervisor = next(s for s in run.steps if s.agent_name == "SupervisorOrchestrator")
        self._complete_step(
            supervisor,
            summary=(
                f"Orchestrator initialized LangGraph-compatible agent pipeline "
                f"(engine={self.engine_name})"
            ),
            details={"pipeline": AGENT_PIPELINE, "orchestratorEngine": self.engine_name},
        )
        run.completed_steps = ["SupervisorOrchestrator"]
        run.current_step = "IntentUnderstandingAgent"
        campaign.status = "RUNNING"
        campaign.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)
        return run

    def execute_campaign_run(
        self,
        run_id: str,
        user_id: str,
        user_role: str,
    ) -> WorkflowRun:
        """Execute agents for a bootstrapped workflow run (used by sync + background workers)."""
        run = self.db.get(WorkflowRun, run_id)
        if not run:
            raise ValueError(f"Workflow run not found: {run_id}")
        campaign = self.db.get(Campaign, run.campaign_id)
        if not campaign:
            raise ValueError(f"Campaign not found for run: {run_id}")

        correlation_id = run.correlation_id
        steps = {s.agent_name: s for s in sorted(run.steps, key=lambda x: x.step_order)}
        state: dict[str, Any] = {
            "workflowRunId": run.id,
            "correlationId": correlation_id,
            "userId": user_id,
            "campaignId": campaign.id,
            "originalRequest": campaign.natural_language_request,
            "maxCustomers": campaign.max_customers,
            "minValueScore": campaign.min_value_score,
            "minPropensityScore": campaign.min_propensity_score,
            "parsedIntent": {},
            "candidateCustomers": [],
            "customerValueResults": [],
            "propensityResults": [],
            "productRecommendations": [],
            "eligibilityResults": [],
            "complianceResults": [],
            "messageDrafts": [],
            "explanations": [],
            "workflowStatus": "RUNNING",
            "currentStep": "SupervisorOrchestrator",
            "completedSteps": list(run.completed_steps or ["SupervisorOrchestrator"]),
            "errors": [],
            "startedAt": run.started_at.isoformat() if run.started_at else datetime.utcnow().isoformat(),
            "completedAt": None,
            "orchestratorEngine": self.engine_name,
        }

        try:
            if self.engine_name == "langgraph":
                state = self._run_langgraph_agents(state, steps, run, user_id, user_role, correlation_id)
            else:
                state = self._run_native_agents(state, steps, run, user_id, user_role, correlation_id)

            ranked = self._rank_candidates(state, campaign)
            state["rankedCustomers"] = ranked
            self._persist_results(campaign, state, ranked)

            approval_step = steps["HumanApproval"]
            approval_step.status = "WAITING_FOR_APPROVAL"
            approval_step.started_at = datetime.utcnow()
            approval_step.summary = (
                f"Waiting for RM approval on {len(state.get('messageDrafts') or [])} message drafts"
            )
            approval_step.processed_records = len(state.get("messageDrafts") or [])
            self.db.flush()

            campaign.status = "WAITING_FOR_APPROVAL"
            campaign.parsed_intent = state.get("parsedIntent")
            intent = state.get("parsedIntent") or {}
            if intent.get("productCategory"):
                campaign.product_category = str(intent["productCategory"])
            elif intent.get("requestedProductCategory"):
                campaign.product_category = str(intent["requestedProductCategory"])
            if intent.get("channel"):
                campaign.channel = str(intent["channel"])
            campaign.updated_at = datetime.utcnow()

            state["workflowStatus"] = "WAITING_FOR_HUMAN_APPROVAL"
            state["currentStep"] = "HumanApproval"
            state["completedAt"] = None

            run.workflow_status = "WAITING_FOR_APPROVAL"
            run.current_step = "HumanApproval"
            run.completed_steps = state["completedSteps"]
            run.state_snapshot = self._safe_snapshot(state)
            self.db.commit()
            self.db.refresh(run)
            return run

        except Exception as exc:  # noqa: BLE001
            state["errors"].append(str(exc))
            run.workflow_status = "FAILED"
            run.errors = state["errors"]
            run.completed_at = datetime.utcnow()
            campaign.status = "FAILED"
            write_audit(
                self.db,
                event_type="WORKFLOW_FAILED",
                summary=f"Workflow failed: {exc}",
                status="FAILED",
                user_id=user_id,
                user_role=user_role,
                correlation_id=correlation_id,
                workflow_run_id=run.id,
                campaign_id=campaign.id,
                agent_name="SupervisorOrchestrator",
            )
            self.db.commit()
            raise

    def run_campaign(
        self,
        campaign: Campaign,
        user_id: str,
        user_role: str,
    ) -> WorkflowRun:
        """Bootstrap + execute synchronously (tests / wait=true clients)."""
        run = self.bootstrap_campaign_run(campaign, user_id=user_id, user_role=user_role)
        return self.execute_campaign_run(run.id, user_id=user_id, user_role=user_role)

    def _run_langgraph_agents(
        self,
        state: dict[str, Any],
        steps: dict[str, WorkflowStep],
        run: WorkflowRun,
        user_id: str,
        user_role: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        graph = build_campaign_graph(self.db, self.llm)
        # Stream node updates so UI workflow steps persist incrementally.
        for event in graph.stream(state, stream_mode="updates"):
            for agent_name, update in event.items():
                if agent_name not in steps:
                    continue
                step = steps[agent_name]
                step.status = "RUNNING"
                step.started_at = datetime.utcnow()
                self.db.flush()
                state.update(update)
                state["currentStep"] = agent_name
                run.current_step = agent_name
                self._complete_step(
                    step,
                    summary=update.get("stepSummary") or f"{agent_name} completed via LangGraph",
                    details={
                        k: update.get(k)
                        for k in update
                        if k not in {"stepSummary", "completedSteps"}
                    },
                    processed_records=int(update.get("processedRecords") or 0),
                )
                write_audit(
                    self.db,
                    event_type="AGENT_COMPLETED",
                    summary=update.get("stepSummary") or f"{agent_name} completed",
                    status="SUCCESS",
                    user_id=user_id,
                    user_role=user_role,
                    correlation_id=correlation_id,
                    workflow_run_id=run.id,
                    campaign_id=run.campaign_id,
                    agent_name=agent_name,
                    metadata={
                        "orchestratorEngine": "langgraph",
                        **extract_agent_telemetry(update),
                    },
                )
                # Persist incrementally so the UI activity log updates while agents run
                self.db.commit()
        state["orchestratorEngine"] = "langgraph"
        return state

    def _run_native_agents(
        self,
        state: dict[str, Any],
        steps: dict[str, WorkflowStep],
        run: WorkflowRun,
        user_id: str,
        user_role: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        agents = [
            IntentUnderstandingAgent(self.llm, db=self.db),
            CustomerRetrievalAgent(self.db),
            CustomerValueAgent(),
            ConversionPropensityAgent(),
            ProductRecommendationAgent(self.db),
            EligibilityAgent(),
            ConsentComplianceAgent(),
            MessageGenerationAgent(self.llm, db=self.db),
            ExplainabilityAgent(),
        ]
        for agent in agents:
            step = steps[agent.name]
            step.status = "RUNNING"
            step.started_at = datetime.utcnow()
            self.db.flush()
            state["currentStep"] = agent.name
            run.current_step = agent.name

            update = agent.run(state)
            state.update(update)
            state["completedSteps"].append(agent.name)

            self._complete_step(
                step,
                summary=update.get("stepSummary") or f"{agent.name} completed",
                details={k: update.get(k) for k in update if k not in {"stepSummary"}},
                processed_records=int(update.get("processedRecords") or 0),
            )
            write_audit(
                self.db,
                event_type="AGENT_COMPLETED",
                summary=update.get("stepSummary") or f"{agent.name} completed",
                status="SUCCESS",
                user_id=user_id,
                user_role=user_role,
                correlation_id=correlation_id,
                workflow_run_id=run.id,
                campaign_id=run.campaign_id,
                agent_name=agent.name,
                metadata={
                    "orchestratorEngine": "native",
                    **extract_agent_telemetry(update),
                },
            )
            self.db.commit()
            # Stop after intent when product is not in catalogue (no Personal Loan stand-in)
            if agent.name == "IntentUnderstandingAgent":
                intent = state.get("parsedIntent") or {}
                if not intent.get("productCategoryResolved") or not intent.get("productCategory"):
                    break
        state["orchestratorEngine"] = "native"
        return state

    def _complete_step(
        self,
        step: WorkflowStep,
        *,
        summary: str,
        details: dict[str, Any] | None = None,
        processed_records: int = 0,
        status: str = "COMPLETED",
    ) -> None:
        step.status = status
        step.summary = summary
        step.details = details or {}
        step.processed_records = processed_records
        step.completed_at = datetime.utcnow()
        if step.started_at:
            step.duration_ms = int((step.completed_at - step.started_at).total_seconds() * 1000)
        else:
            step.started_at = step.completed_at
            step.duration_ms = 0
        self.db.flush()

    def _rank_candidates(self, state: dict[str, Any], campaign: Campaign) -> list[dict[str, Any]]:
        intent = state.get("parsedIntent") or {}
        # If requested product is not in catalogue, return no shortlist (no Personal Loan fallback)
        if not intent.get("productCategoryResolved") or not intent.get("productCategory"):
            state["noDataReason"] = intent.get("productUnavailableMessage") or (
                "No data found for the requested product in the catalogue."
            )
            return []

        values = {r["customerId"]: r for r in (state.get("customerValueResults") or [])}
        props = {r["customerId"]: r for r in (state.get("propensityResults") or [])}
        recs = {r["customerId"]: r for r in (state.get("productRecommendations") or [])}
        eligs = {r["customerId"]: r for r in (state.get("eligibilityResults") or [])}
        comps = {r["customerId"]: r for r in (state.get("complianceResults") or [])}
        explanations = {e["customerId"]: e for e in (state.get("explanations") or [])}
        messages = {m["customerId"]: m for m in (state.get("messageDrafts") or [])}
        profiles = {p["customerId"]: p for p in (state.get("candidateCustomers") or [])}

        ranked = []
        for cid, profile in profiles.items():
            value = values.get(cid, {}).get("overallScore", 0)
            prop = props.get(cid, {}).get("overallScore", 0)
            if value < campaign.min_value_score and prop < campaign.min_propensity_score:
                # keep planted scenarios and high scores anyway for demo visibility
                if profile.get("scenarioTag") not in {"A", "B", "C", "D", "E", "F"} and value < 55:
                    continue
            combined = value * 0.45 + prop * 0.55
            ranked.append(
                {
                    "customerId": cid,
                    "profile": profile,
                    "value": values.get(cid),
                    "propensity": props.get(cid),
                    "recommendation": recs.get(cid),
                    "eligibility": eligs.get(cid),
                    "compliance": comps.get(cid),
                    "explanation": explanations.get(cid),
                    "message": messages.get(cid),
                    "combinedScore": round(combined, 2),
                }
            )

        ranked.sort(key=lambda x: x["combinedScore"], reverse=True)
        return ranked[: campaign.max_customers]

    def _persist_results(
        self,
        campaign: Campaign,
        state: dict[str, Any],
        ranked: list[dict[str, Any]],
    ) -> None:
        for idx, item in enumerate(ranked, start=1):
            profile = item["profile"]
            value = item.get("value") or {}
            prop = item.get("propensity") or {}
            rec = item.get("recommendation") or {}
            elig = item.get("eligibility") or {}
            comp = item.get("compliance") or {}
            explanation = item.get("explanation") or {}
            message = item.get("message")

            self.db.add(
                CampaignCustomer(
                    campaign_id=campaign.id,
                    customer_id=profile["customerId"],
                    rank=idx,
                    value_score=value.get("overallScore"),
                    propensity_score=prop.get("overallScore"),
                    recommended_product_id=rec.get("productId"),
                    eligibility_status=elig.get("status"),
                    compliance_status=comp.get("complianceStatus"),
                    contact_allowed=bool(comp.get("contactAllowed")),
                    explanation=explanation,
                )
            )

            if value:
                self.db.add(
                    CustomerScore(
                        campaign_id=campaign.id,
                        customer_id=profile["customerId"],
                        score_type="VALUE",
                        overall_score=value["overallScore"],
                        classification=value["classification"],
                        component_scores=value.get("componentScores") or {},
                        positive_factors=value.get("positiveFactors") or [],
                        warnings=value.get("warnings") or [],
                        explanation=value.get("explanation") or "",
                    )
                )
            if prop:
                self.db.add(
                    CustomerScore(
                        campaign_id=campaign.id,
                        customer_id=profile["customerId"],
                        score_type="PROPENSITY",
                        overall_score=prop["overallScore"],
                        classification=prop["classification"],
                        component_scores=prop.get("componentScores") or {},
                        positive_factors=prop.get("positiveFactors") or [],
                        negative_factors=prop.get("negativeFactors") or [],
                        warnings=prop.get("warnings") or [],
                        explanation=prop.get("explanation") or "",
                    )
                )
            if rec and rec.get("productId"):
                self.db.add(
                    ProductRecommendation(
                        campaign_id=campaign.id,
                        customer_id=profile["customerId"],
                        product_id=rec["productId"],
                        match_score=rec.get("matchScore") or 0,
                        reason=rec.get("reason") or "",
                        indicative_amount_min=rec.get("indicativeAmountMin") or 0,
                        indicative_amount_max=rec.get("indicativeAmountMax") or 0,
                        indicative_rate=rec.get("indicativeRate") or 0,
                        tenure_min=rec.get("tenureMin") or 0,
                        tenure_max=rec.get("tenureMax") or 0,
                        conditions=rec.get("conditions") or [],
                    )
                )
            if elig:
                self.db.add(
                    EligibilityCheck(
                        campaign_id=campaign.id,
                        customer_id=profile["customerId"],
                        product_id=rec.get("productId") or "",
                        overall_passed=bool(elig.get("overallPassed")),
                        rules=elig.get("rules") or [],
                    )
                )
            if comp:
                self.db.add(
                    ComplianceCheck(
                        campaign_id=campaign.id,
                        customer_id=profile["customerId"],
                        compliance_status=comp.get("complianceStatus") or "BLOCKED",
                        contact_allowed=bool(comp.get("contactAllowed")),
                        failed_checks=comp.get("failedChecks") or [],
                        warnings=comp.get("warnings") or [],
                        explanation=comp.get("explanation") or "",
                        details=comp.get("details") or {},
                    )
                )
            if message:
                self.db.add(
                    MessageDraft(
                        campaign_id=campaign.id,
                        customer_id=profile["customerId"],
                        channel=message.get("channel") or "WHATSAPP",
                        body=message.get("body") or "",
                        status="DRAFT",
                        llm_provider_used=message.get("llmProviderUsed") or "mock",
                    )
                )
        self.db.flush()

    def _safe_snapshot(self, state: dict[str, Any]) -> dict[str, Any]:
        # Keep snapshot compact for SQLite/Postgres
        return {
            "parsedIntent": state.get("parsedIntent"),
            "workflowStatus": state.get("workflowStatus"),
            "completedSteps": state.get("completedSteps"),
            "candidateCount": len(state.get("candidateCustomers") or []),
            "messageCount": len(state.get("messageDrafts") or []),
            "rankedCount": len(state.get("rankedCustomers") or []),
            "errors": state.get("errors") or [],
            "orchestratorEngine": state.get("orchestratorEngine") or self.engine_name,
        }
