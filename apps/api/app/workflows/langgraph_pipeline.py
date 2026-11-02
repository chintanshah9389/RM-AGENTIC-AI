"""LangGraph multi-agent pipeline for Banking CRM orchestration.

Matches the architecture image Agent Orchestrator (LangGraph) while reusing
existing specialized agent modules and DB-backed tools.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
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
from app.llm.base import LLMProvider


class AgentGraphState(TypedDict, total=False):
    workflowRunId: str
    correlationId: str
    userId: str
    campaignId: str
    originalRequest: str
    maxCustomers: int
    minValueScore: float
    minPropensityScore: float
    parsedIntent: dict[str, Any]
    candidateCustomers: list[dict[str, Any]]
    customerValueResults: list[dict[str, Any]]
    propensityResults: list[dict[str, Any]]
    productRecommendations: list[dict[str, Any]]
    eligibilityResults: list[dict[str, Any]]
    complianceResults: list[dict[str, Any]]
    messageDrafts: list[dict[str, Any]]
    explanations: list[dict[str, Any]]
    workflowStatus: str
    currentStep: str
    completedSteps: list[str]
    errors: list[str]
    startedAt: str
    completedAt: str | None
    stepSummary: str
    processedRecords: int
    orchestratorEngine: str


def _merge_agent_result(state: AgentGraphState, update: dict[str, Any], agent_name: str) -> AgentGraphState:
    merged: dict[str, Any] = dict(state)
    merged.update(update)
    completed = list(merged.get("completedSteps") or [])
    if agent_name not in completed:
        completed.append(agent_name)
    merged["completedSteps"] = completed
    merged["currentStep"] = agent_name
    merged["orchestratorEngine"] = "langgraph"
    return merged  # type: ignore[return-value]


def build_campaign_graph(db: Session, llm: LLMProvider):
    """Compile LangGraph StateGraph over specialized banking CRM agents."""

    # Language steps: LangChain create_agent + tools (Intent / Retrieval / Message).
    # Scoring & compliance stay deterministic Python nodes.
    intent_agent = IntentUnderstandingAgent(llm, db=db)
    retrieval_agent = CustomerRetrievalAgent(db)
    value_agent = CustomerValueAgent()
    propensity_agent = ConversionPropensityAgent()
    recommendation_agent = ProductRecommendationAgent(db)
    eligibility_agent = EligibilityAgent()
    compliance_agent = ConsentComplianceAgent()
    message_agent = MessageGenerationAgent(llm, db=db)
    explain_agent = ExplainabilityAgent()

    def intent_node(state: AgentGraphState) -> AgentGraphState:
        return _merge_agent_result(state, intent_agent.run(dict(state)), intent_agent.name)

    def retrieval_node(state: AgentGraphState) -> AgentGraphState:
        return _merge_agent_result(state, retrieval_agent.run(dict(state)), retrieval_agent.name)

    def value_node(state: AgentGraphState) -> AgentGraphState:
        return _merge_agent_result(state, value_agent.run(dict(state)), value_agent.name)

    def propensity_node(state: AgentGraphState) -> AgentGraphState:
        return _merge_agent_result(state, propensity_agent.run(dict(state)), propensity_agent.name)

    def recommendation_node(state: AgentGraphState) -> AgentGraphState:
        return _merge_agent_result(
            state, recommendation_agent.run(dict(state)), recommendation_agent.name
        )

    def eligibility_node(state: AgentGraphState) -> AgentGraphState:
        return _merge_agent_result(state, eligibility_agent.run(dict(state)), eligibility_agent.name)

    def compliance_node(state: AgentGraphState) -> AgentGraphState:
        return _merge_agent_result(state, compliance_agent.run(dict(state)), compliance_agent.name)

    def message_node(state: AgentGraphState) -> AgentGraphState:
        return _merge_agent_result(state, message_agent.run(dict(state)), message_agent.name)

    def explain_node(state: AgentGraphState) -> AgentGraphState:
        return _merge_agent_result(state, explain_agent.run(dict(state)), explain_agent.name)

    graph = StateGraph(AgentGraphState)
    graph.add_node("IntentUnderstandingAgent", intent_node)
    graph.add_node("CustomerRetrievalAgent", retrieval_node)
    graph.add_node("CustomerValueAgent", value_node)
    graph.add_node("ConversionPropensityAgent", propensity_node)
    graph.add_node("ProductRecommendationAgent", recommendation_node)
    graph.add_node("EligibilityAgent", eligibility_node)
    graph.add_node("ConsentComplianceAgent", compliance_node)
    graph.add_node("MessageGenerationAgent", message_node)
    graph.add_node("ExplainabilityAgent", explain_node)

    def after_intent(state: AgentGraphState) -> str:
        intent = state.get("parsedIntent") or {}
        # No catalogue match → stop; never fall through to Personal Loan shortlist
        if intent.get("productCategoryResolved") and intent.get("productCategory"):
            return "CustomerRetrievalAgent"
        return END

    graph.add_edge(START, "IntentUnderstandingAgent")
    graph.add_conditional_edges("IntentUnderstandingAgent", after_intent)
    graph.add_edge("CustomerRetrievalAgent", "CustomerValueAgent")
    graph.add_edge("CustomerValueAgent", "ConversionPropensityAgent")
    graph.add_edge("ConversionPropensityAgent", "ProductRecommendationAgent")
    graph.add_edge("ProductRecommendationAgent", "EligibilityAgent")
    graph.add_edge("EligibilityAgent", "ConsentComplianceAgent")
    graph.add_edge("ConsentComplianceAgent", "MessageGenerationAgent")
    graph.add_edge("MessageGenerationAgent", "ExplainabilityAgent")
    graph.add_edge("ExplainabilityAgent", END)

    return graph.compile()
