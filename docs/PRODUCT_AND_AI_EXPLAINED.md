# RM Agentic AI — Product & AI Explained (Client Guide)

This document explains **what the product is** and **how Agents, LLM, and Tools work**, in plain language, so anyone can understand the POC end to end.

| | |
|--|--|
| **GitHub** | https://github.com/chintanshah9389/RM-AGENTIC-AI |
| **Enterprise architecture diagram** | https://github.com/chintanshah9389/RM-AGENTIC-AI/blob/main/architecture.jpg |
| **Demo video** | https://github.com/chintanshah9389/RM-AGENTIC-AI/blob/main/docs/demo-video/RM-AGENTIC-AI-demo.mp4 |
| **Demo login** | `rm@demo.bank` / `Demo@123` |

> **POC notice:** Synthetic banking data only. Scores/offers are **not** real credit decisions. WhatsApp is **mock only** — no real customer messages are sent.

---

# 1. What is this product?

## 1.1 In one sentence

**RM Agentic AI** is a demonstration Banking CRM where a Relationship Manager asks for outreach in **plain English**, and a **team of AI agents** builds a customer shortlist, checks rules, drafts WhatsApp messages, and waits for the RM to approve before a simulated send.

## 1.2 Problem it solves

Today an RM often has to:

- Manually search for “good” customers  
- Remember product rules (income, risk, eligibility)  
- Check consent before messaging  
- Write WhatsApp text one by one  

This POC shows how **Agentic AI** can support that workflow **with control** — not as a black box that invents products or customers.

## 1.3 What the RM actually does in the app

1. Logs in as Relationship Manager  
2. Optionally browses the customer list (5,000 synthetic profiles)  
3. Starts an **AI campaign** and types a request, for example:  
   > Find high-value customers for a Personal Loan this month and prepare WhatsApp messages.  
4. Watches a **behind-the-scenes** screen while agents run (tools + LLM activity)  
5. Opens the **shortlist** — who is cleared vs blocked, with reasons  
6. Opens a customer → reviews scores, product, eligibility, draft  
7. **Approves** the message → **Mock WhatsApp send** (simulated)  

If the RM asks for a product **not in the catalogue** (e.g. Gold Loan), the system shows **No data found** and does **not** secretly switch to Personal Loan.

## 1.4 What technology the product is built with

| Layer | Technology |
|-------|------------|
| Frontend | React, TypeScript, Vite, Tailwind |
| Backend API | FastAPI (Python) |
| Orchestration | LangGraph (multi-agent workflow) |
| Agent framework | LangChain (`create_agent` + tools) |
| LLM | Mock (offline) or optional NVIDIA API |
| Database | SQLite locally (optional Postgres) |
| Messaging | Mock WhatsApp provider |

## 1.5 Logins (same password: `Demo@123`)

| Role | Email | Meaning |
|------|-------|---------|
| RM | `rm@demo.bank` | Day-to-day: run campaigns, approve, mock send |
| Supervisor | `supervisor@demo.bank` | Oversight/view; cannot run/approve/send in this POC |
| Admin | `admin@demo.bank` | Full demo access (same ops as RM) |

---

# 2. How the AI system works (big picture)

Think of three layers working together:

```text
┌─────────────────────────────────────────────────────────┐
│  1. AGENTS                                              │
│     Specialists that each do one job in a fixed order   │
├─────────────────────────────────────────────────────────┤
│  2. TOOLS                                               │
│     Safe functions that read the database / catalogue   │
├─────────────────────────────────────────────────────────┤
│  3. LLM (Large Language Model)                          │
│     Understands language & helps write text             │
│     — but is checked by validators + rules              │
└─────────────────────────────────────────────────────────┘
```

**Important design rule for this product:**

- The **LLM suggests** (intent JSON, message wording).  
- **Tools fetch real data** (products, customers).  
- **Validators and business rules decide** what is allowed.  
- The **human RM** must approve before mock send.  

So the product is **agentic**, but **governed**.

---

# 3. Agents — in detail

Agents are automated specialists. They run in sequence under a **Supervisor / LangGraph orchestrator**. Each agent updates shared “campaign state,” and the UI can show that live.

## 3.1 Supervisor / Orchestrator

- Starts the campaign workflow when the RM clicks **Start AI campaign**  
- Creates workflow steps so the UI can poll progress  
- Runs the LangGraph pipeline (default)  
- Saves scores, recommendations, eligibility, drafts to the database  
- Stops for **human approval** at the end  
- If the product cannot be resolved from the catalogue → stops early → empty shortlist  

## 3.2 Intent Understanding Agent

**Job:** Understand what the RM asked for.

- Reads the natural-language request  
- Calls tool **`list_active_products`** to see what exists in the catalogue  
- Uses LLM (or mock parser) to propose product, channel, segment, limits  
- Runs **validators** afterward:  
  - Product must match what the RM asked **and** what is in the catalogue  
  - Never silently replace Gold/Car Loan with Personal Loan  

**Output example:** `PERSONAL_LOAN`, channel `WHATSAPP`, segment `HIGH_VALUE`, max customers 10.

## 3.3 Customer Retrieval Agent

**Job:** Find candidate customers from the database.

- Uses tool **`search_customers`** (segment, income, limit)  
- Validates IDs so the model cannot invent people  
- Produces a candidate list for scoring  

## 3.4 Customer Value Agent

**Job:** Score how valuable the customer relationship looks (0–100).

- **No LLM** — transparent heuristic (rules/weights)  
- Factors such as income, tenure, engagement, balances (demo logic)  
- Band for display: roughly Low / Medium / High  

## 3.5 Conversion Propensity Agent

**Job:** Score how likely the customer is to convert this month (0–100).

- Also **deterministic heuristics** (not a production credit model)  
- Used together with value score for ranking the shortlist  

## 3.6 Product Recommendation Agent

**Job:** Pick a concrete product offer inside the **requested category**.

- Example: Personal Loan Standard vs Personal Loan Premium  
- Uses catalogue rules (income thresholds, value score, salary account flags, etc.)  
- Stays inside the resolved category — no random cross-sell  

## 3.7 Eligibility Agent

**Job:** Hard pass/fail against product rules.

Examples of checks:

- Customer active  
- Age within range  
- Minimum monthly income  
- **Maximum risk level** allowed for the product  
- No severe delinquency  
- Minimum customer value score  

A customer can have a “decent” score and still be **ineligible**.

## 3.8 Consent / Compliance Agent

**Job:** Decide if the bank is allowed to contact this customer for promo messaging.

Checks include:

- Marketing consent  
- WhatsApp consent  
- Do-not-contact flag  
- Contacts already made this month vs monthly cap  

If compliance fails → **blocked** (no draft for send).

## 3.9 Message Generation Agent

**Job:** Draft WhatsApp text for cleared contacts only.

- Uses tool **`get_message_context`** (safe fields: first name, product name, city, segment — not raw balances/account numbers)  
- LLM (or mock) writes the message  
- **Message validator** then enforces:  
  - STOP / opt-out language  
  - Eligibility disclaimer  
  - Dummy demonstration notice  
  - Redact long number-like strings  
  - Block phrases like “guaranteed approval”  

## 3.10 Explainability Agent

**Job:** Produce human-readable reasons for the UI.

- Why this customer was shortlisted  
- Why blocked (eligibility vs consent)  
- What the RM should do next (review & approve, etc.)  

---

# 4. Tools — in detail

**Tools** are callable functions agents use to touch real system data. They keep the AI grounded.

| Tool name | What it does | Why it exists |
|-----------|--------------|---------------|
| **`list_active_products`** | Lists active products and categories from DB | Catalogue is source of truth for Intent |
| **`search_customers`** | Searches synthetic Customer360 by segment/income/limit | Retrieval cannot invent customers |
| **`get_customer_360`** | Loads one customer profile (compact) | Rich context when needed |
| **`get_message_context`** | Returns only allowed fields for drafting | Prevents leaking sensitive fields into message generation |

### How tools differ from the LLM

| | Tools | LLM |
|--|-------|-----|
| Nature | Code + database | Language model |
| Output | Structured facts from DB | Suggested text / JSON |
| Trust | High for facts | Must be validated |
| Example | “Catalogue has PERSONAL_LOAN, HOME_LOAN, CREDIT_CARD” | “I think the user wants a personal loan on WhatsApp” |

In this product, **facts win over guesses**.

---

# 5. LLM — in detail

## 5.1 What LLM means here

**LLM (Large Language Model)** = the AI that understands and generates natural language.

In this POC you can run:

- **`mock` provider** — works fully offline; good for demos without API keys  
- **`nvidia` provider** — **POC default for live LLM** via NVIDIA API (NIM / catalog models) when configured  

### 5.1.1 POC LLM vs stronger models (recommendation)

| Stage | Model choice | Why |
|-------|----------------|-----|
| **POC / progressive demo** | **NVIDIA LLM** (already integrated) | Fast to run, cost-effective for demos, enough for intent + draft with our validators |
| **Better quality (recommended next)** | **Claude Sonnet 4.5** (or latest Sonnet) | Strong tool-calling + instruction following; best balance of quality vs cost for agents |
| **Highest reasoning (optional)** | **Claude Opus 4.5 / 4.6** (latest Opus) | Best for harder multi-step reasoning and nuanced intent; higher cost — use when quality matters most |
| **Enterprise alternative** | Azure OpenAI (GPT-4.1 / GPT-4o) or bank-approved private LLM | Often preferred for procurement, data residency, and existing Azure estate |

**Architect recommendation for this product:**

- **Keep NVIDIA for the current POC** so reviewers can run live LLM without changing code.  
- **For a “better results” pilot**, prefer **Claude Sonnet** as the primary upgrade (agents + WhatsApp drafting improve clearly).  
- Use **Claude Opus** only where you need maximum reasoning quality (complex RM phrasing, multi-product intent).  
- Architecture does **not** change — only the LLM provider behind Intent / Message agents. Validators, tools, and human approval stay the same.

## 5.2 Where the LLM is used

1. **Intent stage** — turn RM English into structured campaign intent  
2. **Message stage** — help write WhatsApp draft copy  

## 5.3 Where the LLM is *not* used as the final authority

- Final product category → validators + catalogue  
- Customer list → DB search tool  
- Value / propensity scores → heuristic services  
- Eligibility & consent → hard rules  
- Final message compliance → post-validators  
- Send decision → human RM  

## 5.4 Why this matters for banking-style demos

If the LLM were trusted alone, it might:

- Swap Gold Loan → Personal Loan “to be helpful”  
- Invent customers  
- Promise “guaranteed approval”  

This product is designed so those failure modes are **blocked by architecture** (tools + validators + human approval). Model upgrades improve language quality; **governance still comes from tools + rules + human approval**.

---

# 6. Full happy-path flow (Personal Loan)

```text
1. RM types Personal Loan + WhatsApp request
2. Intent Agent + list_active_products → PERSONAL_LOAN resolved
3. Retrieval Agent + search_customers → candidates from DB
4. Value + Propensity agents → scores
5. Recommendation → Personal Loan Standard/Premium (as applicable)
6. Eligibility → pass/fail rules
7. Compliance → contact allowed?
8. Message Agent → draft (validated)
9. Explainability → reasons on screen
10. RM reviews → Approve → Mock WhatsApp send
```

---

# 7. Governance flow (missing product / empty state)

```text
1. RM asks for Gold Loan (or Car Loan)
2. Intent + catalogue tool → product NOT in catalogue
3. Validator sets productCategoryResolved = false
4. LangGraph stops early (no fake Personal Loan shortlist)
5. UI shows: No data found + available catalogue
```

This is a core product behavior to show reviewers: **AI is helpful only within policy.**

---

# 8. What you will see “behind the scenes”

While the campaign runs, the popup can show lines such as:

- Supervisor started LangGraph  
- Called tool: `list_active_products`  
- Product intent: PERSONAL_LOAN (matched catalogue)  
- Called tool: `search_customers`  
- Produced value scores / propensity / eligibility / compliance  
- Message drafts prepared for cleared contacts  
- Waiting for human approval  

That screen is how we make agents/tools/LLM **visible**, not hidden.

---

# 9. POC vs Enterprise — same architecture, different maturity

**Enterprise target architecture (diagram):**  
https://github.com/chintanshah9389/RM-AGENTIC-AI/blob/main/architecture.jpg  

That diagram shows the full enterprise view (RM UI, data sources, LangGraph orchestrator, specialized agents, tool registry, WhatsApp/CRM outputs, security, and business impact). **Our working POC implements the same control flow** with demo stand-ins (synthetic DB, mock WhatsApp, heuristic scores, NVIDIA/mock LLM).

**Key message for clients:** The POC already uses an **enterprise-shaped pattern** (UI → API → Supervisor/LangGraph → Agents → Tools → LLM → Rules → Human approval → Audit).  

Going enterprise does **not** mean throwing this away. It means **hardening and replacing POC stand-ins** (SQLite, mock WhatsApp, heuristic scores, single-server jobs) with bank-grade systems — while **keeping the same agent/tool/LLM control flow**.

## 9.1 Comparison table

| Area | **This POC (what you see today)** | **Enterprise level (same architecture, productionized)** |
|------|-------------------------------------|----------------------------------------------------------|
| **Purpose** | Demo / take-home / stakeholder review | Production RM / sales / collections outreach platform |
| **Users & access** | 3 demo logins (RM / Supervisor / Admin), JWT | SSO (Azure AD / Okta), fine-grained RBAC, branch/region scopes, maker-checker |
| **UI** | React SPA (Vite) | Same app pattern + design system, accessibility, multi-language, offline-tolerant RM apps |
| **API** | FastAPI monolith on one process | API gateway, versioned services, rate limits, WAF, mTLS between services |
| **Orchestration** | LangGraph in-process + background thread | Same LangGraph/agent graph on **job queue / workers** (Redis/SQS/Kafka), retries, DLQ, SLA timers |
| **Agents** | 9 specialized agents + supervisor | Same agent roles; versioned agent configs; A/B prompts; kill-switches per agent |
| **Tools** | DB tools: products, search, 360, message context | Same tool *contracts* wired to **Core Banking / CRM / CDP / Consent Hub** APIs (not direct SQLite) |
| **LLM** | Mock or **NVIDIA** (POC live LLM) | Stronger models e.g. **Claude Sonnet/Opus** or Azure OpenAI; private VPC, prompt vault, PII gateway, cost controls |
| **Scoring** | Transparent heuristics (demo) | Champion/challenger ML models, feature store, model registry, credit-policy sign-off (where applicable) |
| **Eligibility / compliance** | In-app rules | Policy engine + regulated rule packs; consent from official Consent Management System |
| **Product catalogue** | Seeded `products` table | Master product catalogue / offer management system as system of record |
| **Customer data** | ~5k synthetic Customer360 in SQLite | Real CDC from core/CRM; data residency; masking/tokenization; quality SLAs |
| **Database** | SQLite (local) / optional Postgres | HA Postgres/Oracle, read replicas, encryption at rest, backup/PITR |
| **Messaging** | **Mock WhatsApp** only | WhatsApp Business API / Twilio / Gupshup with templates, opt-out sync, delivery receipts |
| **Human-in-the-loop** | Approve then mock send | Dual control, four-eyes for high-risk segments, case management integration |
| **Audit / logging** | `audit_events` + workflow step activity | Immutable audit, SIEM integration, correlation IDs across services, retention policy |
| **Observability** | Step status + activity log in UI | OpenTelemetry traces, metrics, alerting, agent latency/cost dashboards |
| **Security** | Demo JWT secret, bcrypt users | Secrets manager, key rotation, vulnerability scanning, pen-test, DLP |
| **Environment** | Laptop: API `:8000` + Web `:5173` | Dev / UAT / Prod, blue-green or canary deploys, infra as code |
| **Scale** | Single reviewer / demo load | Thousands of RMs, concurrent campaigns, horizontal workers |
| **Governance (AI)** | Catalogue validators + early stop on unknown product | Same controls + model risk management, prompt change CAB, bias/fairness reviews |
| **What stays the same** | Agent pipeline order, tool-grounding idea, human approval gate, “no silent product substitute” | **Architecture pattern reused** — only integrations and hardening change |

## 9.2 What we reuse vs what we replace

| Reuse from POC (design) | Replace / upgrade for enterprise |
|-------------------------|----------------------------------|
| Multi-agent pipeline (Intent → … → Explain) | Worker fleet + durable workflow state |
| Tool-first grounding (catalogue & customers) | Real bank APIs behind the same tool interfaces |
| Post-LLM validators | Same + stronger PII/policy gateways |
| Human approval before send | Same + richer approval workflows |
| Behind-the-scenes explainability | Same UX + enterprise audit trail |
| Mock WhatsApp / SQLite / heuristic scores | Real channels, HA data store, approved models |

## 9.3 One-line pitch

> **POC proves the agentic architecture works. Enterprise productionizes the same architecture with bank systems, security, scale, and real channels — without changing the core control philosophy.**

---

# 10. Short summary (copy for WhatsApp / email)

**Product:** Agentic Banking CRM POC for Relationship Managers — plain-English campaigns to shortlist + WhatsApp drafts.  

**Agents:** Intent, Retrieval, Value, Propensity, Recommendation, Eligibility, Compliance, Message, Explainability — orchestrated by LangGraph.  

**Tools:** DB-backed `list_active_products`, `search_customers`, `get_customer_360`, `get_message_context`.  

**LLM:** Used for understanding the request and drafting messages (mock or NVIDIA); always checked by validators and business rules.  

**Control:** Catalogue grounding, eligibility, consent, human approval, mock send only, synthetic data.  

**Enterprise path:** Same agent/tool/LLM architecture; swap POC stand-ins (SQLite, mock WhatsApp, heuristics, single server) for HA data, real channels, SSO, queues, and model governance.  

**Proof:** Working app + demo video + HLD/LLD on GitHub.

---

# 11. Suggested email to client

**Subject:** RM Agentic AI POC — product, AI design, and path to enterprise  

Hi [Name],  

Sharing an explanation of the **RM Agentic AI Banking CRM** proof of concept.  

**What it is:** A demo CRM where a Relationship Manager describes a campaign in plain English. A multi-agent system then shortlists synthetic customers, applies eligibility and consent checks, drafts WhatsApp messages, and waits for human approval before a simulated send.  

**How AI works:**  
- **Agents** each handle one step (intent → retrieval → scoring → rules → messaging → explanation).  
- **Tools** read the real product catalogue and customer database so the system doesn’t invent facts.  
- **LLM** helps interpret language and draft text, but validators and banking-style rules control the final outcome.  
- If a product is not in the catalogue (e.g. Gold Loan), the system returns **No data found** instead of substituting another product.  

**POC vs enterprise:** The POC already follows an enterprise-shaped architecture (API + LangGraph agents + tools + LLM + rules + human approval + audit). For production we keep that pattern and upgrade hosting, SSO, core-banking/CRM integrations, real WhatsApp, HA databases, job queues, and model risk controls. See the enterprise diagram and Section 9 comparison table.  

**LLM:** POC uses **NVIDIA** for live language steps (mock offline). For better results we can upgrade to **Claude Sonnet** (recommended) or **Claude Opus** / Azure OpenAI — architecture stays the same.  

**Review materials:**  
- Enterprise architecture diagram: https://github.com/chintanshah9389/RM-AGENTIC-AI/blob/main/architecture.jpg  
- GitHub: https://github.com/chintanshah9389/RM-AGENTIC-AI  
- Demo video: https://github.com/chintanshah9389/RM-AGENTIC-AI/blob/main/docs/demo-video/RM-AGENTIC-AI-demo.mp4  
- Full explanation: https://github.com/chintanshah9389/RM-AGENTIC-AI/blob/main/docs/PRODUCT_AND_AI_EXPLAINED.md  

Demo login: `rm@demo.bank` / `Demo@123`  

Happy to walk through on a call.  

Thanks,  
[Your name]
