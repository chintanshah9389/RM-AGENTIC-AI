# High-Level Design (HLD) — RM Agentic AI Banking CRM

| Field | Value |
|-------|--------|
| Document | High-Level Design |
| Product | RM Agentic AI — Banking CRM POC |
| Version | 1.0 |
| Audience | Architects, reviewers, engineering leads |
| Repo | [chintanshah9389/RM-AGENTIC-AI](https://github.com/chintanshah9389/RM-AGENTIC-AI) |

Related: [LLD.md](./LLD.md) · [agent-workflow.md](./agent-workflow.md) · [architecture.md](./architecture.md)

---

## 1. Purpose & scope

### 1.1 Problem

Relationship Managers (RMs) need to find likely converters for a product, respect eligibility/consent, draft compliant outreach, and keep a human in the loop — without inventing products or customers.

### 1.2 Solution (POC)

A **governed multi-agent campaign system**: the RM describes the goal in natural language; specialized agents + DB tools produce a shortlist, scores, eligibility, WhatsApp drafts, and audit; the RM **approves** before a **mock** send.

### 1.3 In scope

- JWT demo auth (RM / Supervisor / Admin)
- Campaign create → async LangGraph agent run → shortlist → approve → mock WhatsApp
- Synthetic Customer360 + product catalogue (SQLite / optional Postgres)
- Live behind-the-scenes agent/tool telemetry
- Product governance: missing catalogue products → empty shortlist (**No data found**), no silent Personal Loan substitution

### 1.4 Out of scope (deferred)

- Real WhatsApp / Twilio / Salesforce
- Production credit/underwriting models, Feast, pgvector, Redis, S3
- Multi-tenant bank deployment, SSO, full RBAC UI matrix

---

## 2. Goals & non-goals

| Goals | Non-goals |
|-------|-----------|
| Demonstrate agentic orchestration (LangGraph + LangChain tools) | Replace core banking / LOS |
| Explainable heuristic scores | Production ML credit scores |
| Compliance + human approval gates | Unattended auto-send |
| Reviewer-runnable local POC | Horizontal scale / HA |

---

## 3. Personas & roles

| Persona | Login | Access (POC) |
|---------|-------|----------------|
| Relationship Manager | `rm@demo.bank` | Create/run campaigns, approve, mock send |
| Supervisor | `supervisor@demo.bank` | Oversight/view; cannot run/approve/send |
| Admin | `admin@demo.bank` | Same operational rights as RM for demo |

Password for all: `Demo@123`.

---

## 4. System context

```text
┌─────────────┐     HTTPS/JSON      ┌──────────────────┐
│  React Web  │ ◄──────────────────► │  FastAPI API     │
│  (Vite)     │   JWT Bearer         │  /api/v1/*       │
└─────────────┘                      └────────┬─────────┘
                                              │
                     ┌────────────────────────┼────────────────────────┐
                     ▼                        ▼                        ▼
            ┌────────────────┐     ┌──────────────────┐     ┌─────────────────┐
            │ Supervisor +   │     │ SQLAlchemy ORM   │     │ LLM Provider    │
            │ LangGraph      │────►│ SQLite/Postgres  │     │ mock | nvidia   │
            │ Agents+Tools   │     │ Synthetic CRM    │     └─────────────────┘
            └────────┬───────┘     └──────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ Mock WhatsApp  │  (no real send)
            └────────────────┘
```

External actors: **RM (browser)**, optional **NVIDIA API** for LLM, reviewers cloning GitHub.

---

## 5. Logical architecture (layers)

```text
┌────────────────────────────────────────────────────────────┐
│ Presentation   React 18 + TS + Tailwind + TanStack Query   │
├────────────────────────────────────────────────────────────┤
│ API            FastAPI + Pydantic + JWT + CORS             │
├────────────────────────────────────────────────────────────┤
│ Orchestration  SupervisorOrchestrator + LangGraph graph    │
├────────────────────────────────────────────────────────────┤
│ Agents         Intent, Retrieval, Value, Propensity,       │
│                Recommendation, Eligibility, Compliance,    │
│                Message, Explainability                     │
├────────────────────────────────────────────────────────────┤
│ Tools/Services LangChain @tools, scoring, eligibility,     │
│                compliance, messaging, audit, validation    │
├────────────────────────────────────────────────────────────┤
│ Data           SQLAlchemy models · SQLite (default)        │
└────────────────────────────────────────────────────────────┘
```

---

## 6. Major components

| Component | Responsibility |
|-----------|----------------|
| **Web app** (`apps/web`) | Login, dashboard, customers, create campaign, behind-the-scenes modal, workflow, results, customer review/approve |
| **API** (`apps/api`) | Auth, campaigns, workflows, messages, dashboard, system/admin read APIs |
| **SupervisorOrchestrator** | Bootstrap workflow steps, run LangGraph (or native), persist artifacts, rank shortlist, gate human approval |
| **LangGraph pipeline** | Typed `AgentGraphState`; conditional early END if product unresolved |
| **LLM factory** | `mock` (offline) or `nvidia` chat; Intent/Message use LLM + tools |
| **Mock messaging** | Simulated send + disclaimer + audit |
| **Seed scripts** | ~5k synthetic customers, products, demo users |

---

## 7. End-to-end campaign flow (business)

```text
RM login
  → Create campaign (NL request + filters)
  → POST /campaigns + POST /campaigns/{id}/run (async)
  → Behind-the-scenes: live workflow_steps activity
  → Agents:
       Intent (+ catalogue tool) → [if unresolved: empty shortlist]
       → Retrieval → Value → Propensity → Recommend
       → Eligibility → Compliance → Message → Explain
  → Status WAITING_FOR_APPROVAL
  → RM reviews shortlist / customer detail
  → Approve draft → Simulate send
  → Audit trail
```

**Product governance:** if requested product ∉ catalogue → `productCategoryResolved=false` → LangGraph ends after Intent → UI **No data found** (never substitute Personal Loan).

---

## 8. Agent pipeline (high level)

| # | Agent | Nature | Primary I/O |
|---|--------|--------|-------------|
| 0 | SupervisorOrchestrator | Control | Creates `workflow_runs` / steps |
| 1 | IntentUnderstanding | LLM + tool | NL → validated intent |
| 2 | CustomerRetrieval | Tool/DB | Candidates |
| 3 | CustomerValue | Deterministic | Value score 0–100 |
| 4 | ConversionPropensity | Deterministic | Propensity 0–100 |
| 5 | ProductRecommendation | Rules/DB | Product in requested category |
| 6 | Eligibility | Rules | Pass/fail vs product |
| 7 | ConsentCompliance | Rules | Contact allowed? |
| 8 | MessageGeneration | LLM + tool + validator | WhatsApp draft |
| 9 | Explainability | Rules | Why selected / blocked |
| 10 | HumanApproval | Human | Approve / reject / mock send |

---

## 9. Data domains (conceptual)

- **Identity:** users (role-scoped JWT)
- **Customer360:** customers, accounts, transactions, consents, campaign history
- **Catalogue:** products (active categories = source of truth)
- **Campaign runtime:** campaigns, campaign_customers, scores, recommendations, eligibility/compliance checks, message_drafts, approvals, simulated_messages
- **Orchestration:** workflow_runs, workflow_steps (+ activity in step details)
- **Audit:** audit_events

---

## 10. Cross-cutting concerns

| Concern | Approach |
|---------|----------|
| Security | JWT HS256; bcrypt passwords; role checks on mutate APIs; masked account numbers |
| Compliance | Consent hard gate; message validators (STOP, disclaimer, redact); human approval |
| Observability | Workflow step status, activity telemetry, audit events |
| Config | `.env` / pydantic-settings (`LLM_PROVIDER`, `ORCHESTRATOR_ENGINE`, DB URL) |
| CORS | Web origin allow-list for Vite |
| Synthetic data | UI + API banners; demo disclaimer on products/messages |

---

## 11. Deployment topology (POC)

```text
Developer machine / reviewer laptop
  ├── apps/web   → Vite :5173
  ├── apps/api   → Uvicorn :8000
  └── SQLite file agentic_banking_crm.db  (or Docker Postgres)
```

Optional: NVIDIA cloud LLM. No K8s/service mesh in POC.

---

## 12. Quality attributes

| Attribute | Target for POC |
|-----------|----------------|
| Explainability | Heuristic factor lists; eligibility rule results |
| Safety | No real messaging; no product hallucination past validators |
| Runnability | Seed + two processes; README + demo video |
| Extensibility | Swap LLM provider; native vs LangGraph engine |

---

## 13. Risks & mitigations

| Risk | Mitigation |
|------|------------|
| LLM invents product | Post-LLM `validate_intent` + catalogue tool + early END |
| LLM invents customers | Retrieval tool + `validate_candidates` against DB IDs |
| Supervisor blocked from ops | By design; RM/Admin for run/approve |
| SQLite concurrency | Single API process for demo; Postgres path documented |

---

## 14. POC vs Enterprise (same architecture)

The POC uses an **enterprise-shaped** control flow (UI → API → Supervisor/LangGraph → Agents → Tools → LLM → Rules → Human approval → Audit). Enterprise keeps that pattern and upgrades stand-ins.

| Area | POC | Enterprise |
|------|-----|------------|
| Data | Synthetic SQLite / optional Postgres | Core/CRM CDC, HA DB, residency |
| LLM | Mock or NVIDIA NIM | Private/approved LLM + PII gateway |
| Tools | SQLAlchemy DB tools | Same contracts → bank APIs |
| Jobs | In-process thread | Queue workers, retries, DLQ |
| Messaging | Mock WhatsApp | WhatsApp Business + templates |
| Auth | Demo JWT users | SSO + fine RBAC + maker-checker |
| Scores | Heuristics | Registered ML + policy sign-off |
| Ops | Laptop demo | Multi-env, observability, SIEM |

Enterprise target diagram: [architecture.jpg](../architecture.jpg)  
Full client-facing POC vs Enterprise table: [PRODUCT_AND_AI_EXPLAINED.md §9](./PRODUCT_AND_AI_EXPLAINED.md#9-poc-vs-enterprise--same-architecture-different-maturity).

---

## 15. Document map

| Doc | Content |
|-----|---------|
| **HLD** (this) | Context, layers, flows, quality |
| **LLD** | APIs, schema, agent contracts, sequences, modules |
| Demo video | `docs/demo-video/RM-AGENTIC-AI-demo.mp4` |
