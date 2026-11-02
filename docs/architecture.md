# Architecture index (POC)

Authoritative design docs:

| Document | Description |
|----------|-------------|
| **[HLD.md](./HLD.md)** | High-Level Design — context, layers, flows, roles, quality attributes |
| **[LLD.md](./LLD.md)** | Low-Level Design — APIs, schema, agents, tools, sequences, frontend routes |
| [agent-workflow.md](./agent-workflow.md) | Short agent pipeline diagram |
| [DEMO_VIDEO_SCRIPT.md](./DEMO_VIDEO_SCRIPT.md) | Optional narrated demo script |
| [demo-video/RM-AGENTIC-AI-demo.mp4](./demo-video/RM-AGENTIC-AI-demo.mp4) | Live UI walkthrough |

## Stack snapshot

1. **React UI** — RM login, campaign create, live workflow, results, customer 360 + approval  
2. **FastAPI** — auth, campaigns, workflow, messages, audit, health  
3. **Supervisor + LangGraph** — typed workflow state + step persistence  
4. **Specialized agents** — intent → retrieval → scores → product → eligibility → compliance → message → explainability  
5. **Tools / services** — SQLAlchemy, scoring, rules, mock messaging  
6. **LLM** — NVIDIA (optional) + Mock fallback  

Default DB: **SQLite**; optional **PostgreSQL** via Docker. WhatsApp: **mock only**.
