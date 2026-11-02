from app.workflows.langgraph_pipeline import build_campaign_graph
from app.llm.mock_provider import MockLLMProvider
from app.db.session import SessionLocal


def test_langgraph_pipeline_compiles_and_runs():
    db = SessionLocal()
    try:
        graph = build_campaign_graph(db, MockLLMProvider())
        result = graph.invoke(
            {
                "originalRequest": (
                    "Find high-value customers likely to convert for a Personal Loan "
                    "this month and prepare personalized WhatsApp messages."
                ),
                "maxCustomers": 5,
                "minValueScore": 60,
                "minPropensityScore": 50,
                "completedSteps": [],
                "errors": [],
                "workflowStatus": "RUNNING",
            }
        )
        assert result.get("orchestratorEngine") == "langgraph"
        assert "IntentUnderstandingAgent" in (result.get("completedSteps") or [])
        assert "ExplainabilityAgent" in (result.get("completedSteps") or [])
        assert result.get("parsedIntent", {}).get("productCategory") == "PERSONAL_LOAN"
        assert isinstance(result.get("candidateCustomers"), list)
    finally:
        db.close()
