# BUILD STATUS — Agentic AI Banking CRM (MVP)

## Locked decisions
- Scope: Trimmed MVP for take-home assignment
- LLM: `mock` default + optional `nvidia` + automatic mock fallback
- Orchestration: Typed state-machine Supervisor
- Messaging: MockWhatsApp only
- DB: SQLite (Postgres-ready SQLAlchemy models)

## Phase status

| Phase | Status | Notes |
|-------|--------|-------|
| 0 Inspect architecture | COMPLETED | architecture.jpg mapped |
| 1 Skeleton + DB + seed | COMPLETED | 50 customers, scenarios A–F |
| 2 Domain engines/tools | COMPLETED | scoring/eligibility/compliance/recommendation |
| 3 Agents + orchestrator | COMPLETED | full pipeline + persistence |
| 4 API routes | COMPLETED | auth/campaign/workflow/messages/audit/health |
| 5 React MVP UI | COMPLETED | login/dashboard/create/workflow/results/customer |
| 6 Tests + README + verify | COMPLETED | pytest 5 passed; vitest passed; e2e_smoke OK |

## Verification
- Seed: 50 customers / 74 accounts / 550 txns / 3 products
- Backend tests: 5 passed
- Frontend tests: 1 passed
- E2E API smoke: login → campaign → workflow → approve Priya (A) → mock send OK; Meera (F) blocked
- API running: http://127.0.0.1:8000

## Browser verification (COMPLETED)
- Frontend + API running
- Fixed CORS / Vite proxy (`/api/v1`)
- Login → Create campaign → Live workflow → Results (Priya S-A) → Approve → Simulate Send
- Message status reached `SIMULATED_SENT`

## NVIDIA integration (COMPLETED)
- API key generated (`agentic-banking-crm`) and stored in `apps/api/.env` (gitignored)
- Working model: `nvidia/nemotron-3.5-bolt-e4b` (older llama-3.1-8b-instruct is EOL)
- Verified: intent parsing + WhatsApp message generation via NVIDIA
- Fallback to Mock still active if NVIDIA fails

## LangGraph + PostgreSQL (COMPLETED)
- LangGraph orchestrator default (`ORCHESTRATOR_ENGINE=langgraph`)
- langchain-core installed as LangGraph dependency
- Health reports `orchestratorEngine=langgraph`, `framework.langgraph=true`
- PostgreSQL added to `infra/docker-compose.yml` (start Docker Desktop to use)
- Local default remains SQLite; SQLAlchemy models are Postgres-compatible
- Tests: 6 passed (includes LangGraph pipeline test)

## Next exact step
1. Start Docker Desktop if you want Postgres: `docker compose -f infra/docker-compose.yml up --build`
2. Record demo video using `docs/demo-script.md`
3. Push to GitHub when ready (do not commit `.env`)

