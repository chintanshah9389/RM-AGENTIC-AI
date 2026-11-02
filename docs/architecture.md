# Architecture (POC)

This project implements the **agentic core** of the attached banking CRM architecture image.

## Layers

1. **React UI** — RM login, campaign create, live workflow, results, customer 360 + approval
2. **FastAPI** — auth, campaigns, workflow, messages, audit, health
3. **Supervisor + LangGraph Orchestrator** — typed workflow state + step persistence
4. **Specialized agents** — intent, retrieval, value, propensity, product, eligibility, compliance, message, explainability
5. **Tools / services** — SQLAlchemy repositories, scoring, rules, mock messaging
6. **LLM providers** — NVIDIA (optional) + Mock fallback

## Orchestration (matches architecture image)

- Default engine: **LangGraph** (`ORCHESTRATOR_ENGINE=langgraph`)
- Fallback engine: native sequential runner (`ORCHESTRATOR_ENGINE=native`)
- LangGraph nodes wrap the same specialized agent modules
- Supervisor still owns DB persistence, ranking, human-approval gate, audit

## Data stand-ins

| Architecture source | POC implementation |
|---------------------|--------------------|
| CRM / Core Banking | SQLAlchemy models + seeded synthetic data |
| PostgreSQL | **SQLite** local default; **PostgreSQL** via Docker Compose |
| Redis / Feast / pgvector / S3 | Deferred (documented future) |
| Consent | `customer_consents` |
| Product catalogue | `products` |
| WhatsApp / Twilio | MockWhatsAppProvider |
| Salesforce | omitted (future) |

## Free-first stack mapping

| Image item | Free POC choice |
|------------|-----------------|
| OpenAI / Azure / Claude | NVIDIA NIM free API + Mock |
| LangGraph / LangChain | LangGraph + langchain-core |
| PostgreSQL | SQLite or Docker Postgres |
| WhatsApp Business | Mock WhatsApp |

## Guardrails

- Compliance hard-blocks outbound messaging
- Human approval required before mock send
- Synthetic data banners throughout UI/API
