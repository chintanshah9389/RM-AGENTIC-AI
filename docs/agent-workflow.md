# Agent workflow

```
START
 → Supervisor
 → IntentUnderstandingAgent
 → CustomerRetrievalAgent
 → CustomerValueAgent
 → ConversionPropensityAgent
 → ProductRecommendationAgent
 → EligibilityAgent
 → ConsentComplianceAgent
 → MessageGenerationAgent (only if eligible + contact allowed)
 → ExplainabilityAgent
 → WAITING_FOR_HUMAN_APPROVAL
 → Approve / Reject
 → Mock WhatsApp (approved only)
 → COMPLETE
```

Each agent returns typed partial state. Orchestrator persists workflow_steps and campaign artifacts.
