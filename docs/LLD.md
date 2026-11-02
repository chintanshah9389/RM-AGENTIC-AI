# Low-Level Design (LLD) — RM Agentic AI Banking CRM

| Field | Value |
|-------|--------|
| Document | Low-Level Design |
| Product | RM Agentic AI — Banking CRM POC |
| Version | 1.0 |
| Audience | Backend/frontend engineers implementing or extending the POC |
| Companion | [HLD.md](./HLD.md) |

---

## 1. Repository & runtime modules

```text
apps/
  api/                         # FastAPI backend
    app/
      main.py                  # App factory, CORS, exception handlers
      api/v1/                  # HTTP routers
      agents/                  # Specialized agents + validation + schemas
      workflows/               # SupervisorOrchestrator + LangGraph
      tools/                   # LangChain tools + customer_tools DB helpers
      services/                # scoring, eligibility, compliance, messaging, audit, activity
      llm/                     # mock / nvidia / chat_factory
      models/entities.py       # SQLAlchemy tables
      schemas/                 # Pydantic request/response
      core/                    # config, security, response envelope
      db/                      # engine / SessionLocal
    scripts/seed_database.py
  web/                         # React + Vite frontend
    src/pages/                 # Login, Dashboard, Customers, Campaign, Workflow, Results, Detail
    src/components/            # BehindScenesSetupModal, AgentActivityLog, wizards, toasts
docs/
  HLD.md  LLD.md  DEMO_VIDEO_SCRIPT.md  demo-video/
```

**Processes**

| Process | Command (typical) | Port |
|---------|-------------------|------|
| API | `uvicorn app.main:app` (`PYTHONPATH=.`) | 8000 |
| Web | `npm run dev` (Vite) | 5173 |

---

## 2. API design

Base path: `/api/v1`  
Envelope: `{ "success": bool, "data": ..., "message"?: string }` (see `app/core/response.py`)  
Auth: `Authorization: Bearer <JWT>` except login/health.

### 2.1 Auth

| Method | Path | Roles | Notes |
|--------|------|-------|-------|
| POST | `/auth/login` | public | email/password → access_token + user |
| GET | `/auth/me` | any | Current user |
| POST | `/auth/logout` | any | Audit logout |

JWT claims: subject=`user.id`, `role`, `email`. Expiry from settings.

### 2.2 Campaigns & workflows

| Method | Path | Roles | Notes |
|--------|------|-------|-------|
| POST | `/campaigns` | RM, Supervisor, Admin | Create DRAFT campaign |
| GET | `/campaigns` | any auth | List |
| GET | `/campaigns/{id}` | any auth | Detail + parsedIntent |
| DELETE | `/campaigns/{id}` | RM, Supervisor, Admin | Cascade cleanup |
| POST | `/campaigns/{id}/run` | **RM, Admin** | Default **async** bootstrap + background thread; `?wait=true` sync |
| GET | `/campaigns/{id}/results` | any auth | Shortlist projection; empty + message if product unresolved |
| GET | `/workflows/{id}` | any auth | Run status |
| GET | `/workflows/{id}/steps` | any auth | Steps + activity telemetry |

### 2.3 Messages & audit

| Method | Path | Roles | Notes |
|--------|------|-------|-------|
| PATCH | `/messages/{id}` | RM, Admin | Edit draft body |
| POST | `/messages/{id}/approve` | RM, Admin | Requires contact_allowed |
| POST | `/messages/{id}/reject` | RM, Admin | |
| POST | `/messages/{id}/simulate-send` | RM, Admin | Mock provider only |
| GET | `/audit-events` | any auth | Filterable audit |

### 2.4 Dashboard / system

| Method | Path | Notes |
|--------|------|-------|
| GET | `/dashboard/summary` | Counts for home cards |
| GET | `/customers` … | Customer browse (see campaigns/customers routers as implemented) |
| GET | `/admin/products`, `/admin/rules` | Catalogue/rules visibility |

### 2.5 Create campaign payload (LLD)

```json
{
  "name": "string",
  "natural_language_request": "string",
  "product_category": "AUTO",
  "channel": "AUTO",
  "max_customers": 10,
  "min_value_score": 50,
  "min_propensity_score": 40
}
```

`AUTO` means Intent agent + validators resolve product/channel from NL + catalogue (not a hardcoded form enum).

---

## 3. Async run sequence

```text
UI                         API                         Background thread
 │                          │                                │
 │ POST /campaigns          │                                │
 │─────────────────────────►│ persist Campaign               │
 │◄─────────────────────────│                                │
 │ POST /campaigns/{id}/run │                                │
 │─────────────────────────►│ bootstrap WorkflowRun+Steps    │
 │◄── { status:RUNNING,     │ start Thread ─────────────────►│
 │      async:true }        │                                │ execute_campaign_run
 │ GET .../steps (poll)     │◄──────── persist step updates ─│
 │◄── activity lines        │                                │ LangGraph invoke
 │                          │◄──────── CampaignCustomer etc ─│
 │ Continue → /results      │◄──────── WAITING_FOR_APPROVAL ─│
```

**UI:** `BehindScenesSetupModal` polls workflow steps and renders `AgentActivityLog` until continue is enabled.

---

## 4. Orchestration LLD

### 4.1 Classes

- `SupervisorOrchestrator` (`workflows/orchestrator.py`)
  - `bootstrap_campaign_run` → PENDING/RUNNING steps for `AGENT_PIPELINE`
  - `execute_campaign_run` → LangGraph or native; persist scores/recs/eligibility/compliance/messages; rank; set `WAITING_FOR_APPROVAL`
  - Early path: if intent unresolved → empty shortlist artifacts + completion toward approval/empty UI

- `build_campaign_graph(db, llm)` (`workflows/langgraph_pipeline.py`)
  - Nodes wrap agent `.run(state)`
  - Conditional after Intent: resolved → Retrieval; else → `END`

### 4.2 `AgentGraphState` (key fields)

| Field | Type | Producer |
|-------|------|----------|
| `originalRequest` | str | Supervisor |
| `parsedIntent` | dict | Intent + validation |
| `candidateCustomers` | list | Retrieval |
| `customerValueResults` | list | Value |
| `propensityResults` | list | Propensity |
| `productRecommendations` | list | Recommendation |
| `eligibilityResults` | list | Eligibility |
| `complianceResults` | list | Compliance |
| `messageDrafts` | list | Message |
| `explanations` | list | Explainability |
| `completedSteps` | list[str] | Graph merge |

### 4.3 Engine switch

`ORCHESTRATOR_ENGINE=langgraph` (default) | `native`  
Native runs the same agents sequentially without LangGraph edges.

---

## 5. Agent contracts

### 5.1 IntentUnderstandingAgent

- **Tools:** `list_active_products`
- **LLM:** structured/JSON intent (or mock parse)
- **Post:** `validate_intent(...)` — catalogue + request grounding win
- **Outputs:** `parsedIntent` with  
  `productCategory`, `productCategoryResolved`, `productCategorySource`,  
  `requestedProductCategory`, `productUnavailableMessage`,  
  `customerSegment`, `channel`, `maximumCustomers`, score mins, `validated`

### 5.2 CustomerRetrievalAgent

- **Tools:** `search_customers(segment_hint, min_income, limit)`
- **Post:** `validate_candidates` (unique IDs, limit)
- **Outputs:** `candidateCustomers`

### 5.3 CustomerValueAgent / ConversionPropensityAgent

- **Service:** `services/scoring.py` heuristics
- **Classification:** LOW &lt;40 · MEDIUM 40–69 · HIGH ≥70 (display)
- **Persist:** `customer_scores` rows

### 5.4 ProductRecommendationAgent

- Catalogue products filtered by intent category
- Thresholds: income, value score, salary account flags
- **Persist:** `product_recommendations`

### 5.5 EligibilityAgent

- Rules vs product: active, age, income, **max risk category**, delinquency, min value score, etc.
- **Persist:** `eligibility_checks` (`overall_passed`, `rules[]`)

### 5.6 ConsentComplianceAgent

- marketing/whatsapp consent, DNC, contact frequency
- Sets `contact_allowed`
- **Persist:** `compliance_checks`

### 5.7 MessageGenerationAgent

- Tool: `get_message_context` (safe fields only)
- LLM or template draft
- **Post:** `validate_message_body` (STOP, eligibility wording, redact long digits, no “guaranteed approval”)
- Only for eligible + contact allowed
- **Persist:** `message_drafts` status `DRAFT`

### 5.8 ExplainabilityAgent

- Builds human-readable reasons / required actions (`RM_REVIEW_AND_APPROVE`, blocked reasons)
- Stored on `campaign_customers.explanation`

---

## 6. Tools LLD

`build_crm_tools(db)` → LangChain `@tool` wrappers:

| Tool | Backing function | Returns |
|------|------------------|---------|
| `list_active_products` | `get_active_products` | JSON products + `availableCategories` |
| `search_customers` | `retrieve_candidate_customers` | JSON customer summaries |
| `get_customer_360` | `get_customer_360_by_id` | Compact profile JSON |
| `get_message_context` | inline rules payload | Allowed draft fields |

Invocation helper: `invoke_tool(tool, **kwargs)`.

---

## 7. Validation LLD (`agents/validation.py`)

| Function | Responsibility |
|----------|----------------|
| `detect_requested_product` | NL → canonical category (incl. generic `* loan`; **no** PL default) |
| `resolve_product_category` | Request + catalogue; sources like `request_catalogue_match`, `not_in_catalogue:X` |
| `validate_intent` | Normalize segment/channel/limits/scores; set resolved flags + unavailable message |
| `validate_candidates` | Dedupe IDs, optional allow-list, limit |
| `validate_message_body` | Compliance copy + redaction |

---

## 8. Data model (logical ER)

```text
users ─┬─< campaigns ─┬─< campaign_customers >─ customers
       │              ├─< customer_scores
       │              ├─< product_recommendations >─ products
       │              ├─< eligibility_checks
       │              ├─< compliance_checks
       │              ├─< message_drafts ─┬─< approval_decisions
       │              │                   └─< simulated_messages
       │              └─< workflow_runs ───< workflow_steps
       │
customers ─┬─< accounts
           ├─< transactions
           ├─< customer_consents
           └─< campaign_history

audit_events (loose FKs by id fields)
```

### 8.1 Important enums / statuses

| Entity | Values (POC) |
|--------|----------------|
| `users.role` | `RELATIONSHIP_MANAGER`, `SUPERVISOR`, `ADMIN` |
| `campaigns.status` | `DRAFT`, running-derived, etc. |
| `workflow_runs.workflow_status` | `PENDING`, `RUNNING`, `WAITING_FOR_APPROVAL`, `COMPLETED`, `FAILED` |
| `workflow_steps.status` | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED` |
| `message_drafts.status` | `DRAFT`, `APPROVED`, `REJECTED`, `SIMULATED_SENT` |
| `customers.risk_category` | `HIGH`, `MEDIUM`, `LOW` |
| Product categories (seed) | `PERSONAL_LOAN`, `HOME_LOAN`, `CREDIT_CARD` (+ ensure script) |

### 8.2 Shortlist ranking (orchestrator)

Composite of value + propensity; filters by `max_customers`, min scores; `contact_allowed` drives “Review & approve” vs blocked.

---

## 9. Frontend LLD

### 9.1 Routes

| Path | Page | Purpose |
|------|------|---------|
| `/login` | LoginPage | Demo chips + JWT store |
| `/` | DashboardPage | Stats + recent campaigns |
| `/customers` | CustomersPage | Browse Customer360 |
| `/customers/:id` | CustomerBrowseDetailPage | Read-only detail |
| `/campaigns/new` | CreateCampaignPage | Form + BehindScenesSetupModal |
| `/campaigns/:id/workflow/:wid` | WorkflowPage | Step progress |
| `/campaigns/:id/results` | ResultsPage | Shortlist / empty state / delete |
| `/campaigns/:id/customers/:cid` | CustomerDetailPage | Scores, draft, approve, mock send |

### 9.2 Key components

- `BehindScenesSetupModal` — polls steps; enables “Continue to shortlist preview”
- `AgentActivityLog` — tool/LLM/agent lines from step `details`/activity
- `RmJourneyWizard` — 5-step RM journey chrome
- `ConfirmDeleteModal` — campaign delete confirm
- Auth: `useAuth` + localStorage token; `api` client attaches Bearer

### 9.3 Empty state UX

When results API signals unresolved product / no rows: show **No data found** + available catalogue; CTA “Try another campaign request”.

---

## 10. Messaging LLD

`get_messaging_provider()` → `MockWhatsAppProvider`:

1. Requires approved message + contact allowed  
2. Writes `simulated_messages`  
3. Sets draft status `SIMULATED_SENT`  
4. Audit `MESSAGE_SIMULATED_SENT` (or equivalent)  
5. Returns disclaimer: no real customer message  

---

## 11. Configuration (settings)

| Key | Default | Meaning |
|-----|---------|---------|
| `DATABASE_URL` | sqlite file | SQLAlchemy URL |
| `LLM_PROVIDER` | `mock` | `mock` \| `nvidia` |
| `NVIDIA_API_KEY` / model / base URL | — | Optional live LLM |
| `ORCHESTRATOR_ENGINE` | `langgraph` | `langgraph` \| `native` |
| `MESSAGING_PROVIDER` | `mock` | Mock only in POC |
| `JWT_*` | dev secret | Auth |
| `CORS_ORIGINS` | Vite localhost | Browser access |
| `CUSTOMER_SEED_COUNT` | 5000 | Seed size |

---

## 12. Security LLD

- Passwords: bcrypt via `hash_password` / `verify_password`
- `require_roles(*roles)` dependency raises 403 if role mismatch
- Account numbers stored/shown **masked**
- Message validator strips long digit runs
- `.env` gitignored; do not commit API keys or `.db` if sensitive (POC DB is synthetic)

---

## 13. Observability LLD

- **WorkflowStep.details** + activity helpers (`services/activity_log.py`) — kinds: agent, tool, llm, info  
- **AuditEvent** — campaign create/delete, approvals, sends, login  
- Correlation: `workflow_runs.correlation_id`  

---

## 14. Error handling patterns

| Case | Behavior |
|------|----------|
| Product not in catalogue | Intent unresolved → graph END → empty results + message |
| Compliance fail | No draft / contact_allowed false → blocked UI |
| NVIDIA model errors | Fall back toward mock paths where implemented |
| Approve on blocked | API 400 |
| Edit after simulated send | API 400 |

---

## 15. Test & verification hooks

- `apps/api/tests/` — scoring/compliance, LangGraph pipeline  
- `apps/web/tests/` — login  
- Manual: demo video script + `docs/demo-video/record_live_demo.py`  
- Seed: `python scripts/seed_database.py`

---

## 16. Extension guidelines

1. **New product category** — seed `products`, extend `REQUEST_PRODUCT_HINTS` if needed; no UI hardcode required.  
2. **New agent** — implement `run(state)`, register LangGraph node + `AGENT_PIPELINE` + persistence in orchestrator.  
3. **New tool** — add in `langchain_tools.py` + wire to agent.  
4. **Real WhatsApp** — implement provider interface parallel to mock; keep approval gate.

---

## 17. Traceability (HLD → code)

| HLD concept | Primary code |
|-------------|--------------|
| Web layer | `apps/web/src` |
| API layer | `apps/api/app/api/v1` |
| Supervisor | `workflows/orchestrator.py` |
| LangGraph | `workflows/langgraph_pipeline.py` |
| Agents | `app/agents/*` |
| Tools | `app/tools/*` |
| Validation | `agents/validation.py` |
| Schema | `models/entities.py` |
