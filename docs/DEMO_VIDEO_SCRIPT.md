# Demo video script — RM Agentic AI

Use this as a **teleprompter + click path** for Loom, OBS, or Zoom recording.  
Target length: **10–12 minutes**. Speak clearly; pause ~1s after each major click.

**GitHub:** https://github.com/chintanshah9389/RM-AGENTIC-AI  
**Login:** `rm@demo.bank` / `Demo@123`  
**URLs:** Web http://localhost:5173 · API http://localhost:8000/docs

---

## Before you hit Record

1. Start API + web (see README).
2. Clear or leave a few old campaigns (optional: delete old ones for a clean Results list).
3. Browser: 1280×720 or full HD, zoom 100%, hide bookmarks bar.
4. Open two tabs ready: app home + (optional) API docs — you only need the app for the main take.
5. Close Slack/email popups. Do not show `.env` or API keys on screen.

**Recording tip:** Loom “Screen + Cam” is fine for intros; then switch to screen-only for the workflow so the UI stays readable.

---

## Scene map (timeline)

| # | Time | Scene | On screen |
|---|------|-------|-----------|
| 0 | 0:00–0:45 | Hook + problem | Title / home |
| 1 | 0:45–1:30 | What we built | Home + brief scroll |
| 2 | 1:30–2:15 | Tech stack (short) | Optional: README or just speak |
| 3 | 2:15–3:00 | Login + Customers | Login → `/customers` |
| 4 | 3:00–5:30 | Happy path campaign | Create → Behind-the-scenes → Workflow → Results |
| 5 | 5:30–7:30 | Agent-by-agent deep dive | Results / behind-scenes log / explain |
| 6 | 7:30–8:45 | Problem we solved: no fake product | Gold/Car Loan → No data found |
| 7 | 8:45–10:00 | Eligibility / risk / scores | Pick Kavya or similar ineligible row |
| 8 | 10:00–10:45 | Human approval + audit | Approve / mock send |
| 9 | 10:45–11:30 | Close + how to run | Repo + README |

---

## SCENE 0 — Hook (0:00)

**Do:** Show the home page (logged out or logged in). Brand visible.

**Say:**

> Hi — this is a demo of **RM Agentic AI**, an agentic banking CRM proof of concept.  
> Relationship Managers today waste time hunting for the right customers, checking product rules by hand, and drafting compliant outreach.  
> We built a governed multi-agent workflow: the RM types a request in plain English, and the system shortlists customers, scores them, checks eligibility and consent, drafts WhatsApp messages, and waits for a human before anything is “sent.”  
> Important: this uses **synthetic Indian banking data** only. No real credit decisions. No real WhatsApp sends.

---

## SCENE 1 — What we solved (0:45)

**Do:** Stay on home; point at “create campaign” / main CTA if visible.

**Say:**

> In this POC we specifically solved:
>
> 1. **Natural-language campaign setup** — no long form of product codes.  
> 2. **Multi-agent orchestration** — Intent, Retrieval, Scoring, Recommendation, Eligibility, Compliance, Messaging, Explainability.  
> 3. **Tool use** — agents call real DB-backed tools: list products, search customers, get customer 360, get message context.  
> 4. **LLM validation** — we do **not** trust the model blindly. Post-LLM validators ground product and channel against the catalogue and the RM’s words.  
> 5. **No silent product substitution** — if someone asks for Gold Loan or Car Loan and it is not in the catalogue, we show **No data found**, not Personal Loan.  
> 6. **Live behind-the-scenes telemetry** — while agents run, the RM sees which agent and which tools fired.  
> 7. **Human-in-the-loop** — approval before mock send, with an audit trail.

---

## SCENE 2 — Tech stack (1:30) — keep short

**Do:** Optional: flash README “Tech stack” table for 5 seconds, then back to app.

**Say:**

> Stack in one line: React and Vite on the front, FastAPI and SQLAlchemy on the back, SQLite for local demo, LangGraph for the workflow, LangChain agents with tools, mock LLM offline or optional NVIDIA LLM, JWT demo login.

---

## SCENE 3 — Login + data (2:15)

**Do:**
1. Open login.
2. Enter `rm@demo.bank` / `Demo@123`.
3. Go to **Customers**.
4. Scroll; point at account type / account number columns.

**Say:**

> Demo login is the Relationship Manager persona.  
> Under Customers you see synthetic Customer360 profiles — income, segment, risk category, and account type and number so reviewers can verify the data is real in the DB, not hard-coded on one screen.  
> Behind this is a seeded SQLite database with thousands of customers and an active product catalogue.

---

## SCENE 4 — Happy path: Personal Loan campaign (3:00)

### 4a — Create campaign

**Do:** Start **Create campaign** / new campaign flow.  
Paste (or type) exactly:

```text
Find high-value customers likely to convert for a Personal Loan this month and prepare personalized WhatsApp messages. Limit to 8 customers.
```

**Say:**

> The RM does not pick product codes from a dropdown. They describe the goal. Personal Loan is in our catalogue, so this should resolve cleanly.

### 4b — Behind-the-scenes modal (while agents run)

**Do:** Submit / run. Keep the **Start Campaign / behind-the-scenes** popup open. Do **not** rush past it. Scroll the live log slowly.

**Say:**

> As soon as the run starts, you see a live activity feed — not after the fact on a separate “AI working” wall of noise.  
> Watch for:
>
> - **Intent agent** calling **`list_active_products`** — catalogue is the source of truth.  
> - Parsed intent: product category `PERSONAL_LOAN`, channel WhatsApp, segment high-value, max customers capped.  
> - **`productCategoryResolved: true`** — validators confirmed catalogue match.  
> - **Retrieval agent** calling **`search_customers`**.  
> - Scoring and recommendation steps.  
> - Eligibility and compliance gates.  
> - Message agent using **`get_message_context`** then drafting text with STOP and eligibility disclaimer.
>
> This is how we show stakeholders that agents are tool-using workers, not a single black-box prompt.

### 4c — Workflow page

**Do:** When allowed, open the workflow / AI working view. Point at completed steps. Note that “Open results anytime” stays hidden until agents finish (if that UI rule is still in place).

**Say:**

> The workflow page shows progress through the LangGraph pipeline. We only unlock results when the agent run has finished, so the shortlist is complete and consistent.

### 4d — Results

**Do:** Open Results. Scroll the shortlist. Open one customer’s explainability / reasons. Point at scores and recommendation.

**Say:**

> Results show who made the shortlist, customer value and propensity scores, recommended product in the **requested** category, eligibility, and why they were selected.  
> Scores are transparent heuristics for the POC — explainable to an RM, not a hidden neural score.

---

## SCENE 5 — Agent behavior deep dive (5:30)

**Do:** Stay on Results or reopen behind-scenes history for that campaign. Speak to each step while pointing.

**Say:**

> Walking the agents one by one:
>
> **1. Intent Understanding** — LLM proposes structured intent; then `validate_intent` runs. Request text detection and catalogue win over model guesses. Channel and segment are normalized; max customers clamped.
>
> **2. Customer Retrieval** — LangChain tool `search_customers` hits the DB. Candidates are re-validated so IDs must exist — the model cannot invent customers.
>
> **3. Customer Value Scoring** — deterministic service, 0–100, with factors an RM can discuss.
>
> **4. Conversion Propensity** — same idea for likelihood to convert this month.
>
> **5. Product Recommendation** — scoped to the resolved catalogue category, not a random cross-sell.
>
> **6. Eligibility** — hard rules: income, age, risk band, delinquency, product limits. Failed eligibility means not contactable for this offer even if the score looks okay.
>
> **7. Consent / Compliance** — promotional contact only if consent allows; compliance is a hard gate.
>
> **8. Message Generation** — drafts WhatsApp copy; `validate_message_body` enforces opt-out, disclaimer, redacts long number-like strings, blocks “guaranteed approval.”
>
> **9. Explainability** — human-readable reasons for selection.
>
> **10. Human approval** — nothing is treated as sent until the RM approves; then a **mock** WhatsApp provider logs the send for audit.

---

## SCENE 6 — Problem solved: missing catalogue product (7:30)

**Do:** Create a **second** campaign. Prompt:

```text
Find high-value customers for a Gold Loan this month and prepare WhatsApp messages.
```

(Or **Car Loan** if you prefer.) Keep behind-the-scenes open.

**Say:**

> Earlier models sometimes “helpfully” swapped in Personal Loan when Gold or Car Loan was missing. That is dangerous in banking demos — it looks like the AI invents products.  
> Watch the intent step: tools still list active products; validators set **`productCategoryResolved` to false**; source looks like `not_in_catalogue:GOLD_LOAN`.  
> Shortlist stays empty with a clear **No data found** message. No Personal Loan fallback. That is deliberate product governance.

**Do:** Show empty results / message. Optionally delete this campaign with the confirm modal to show cleanup.

---

## SCENE 7 — Eligibility ≠ high score (8:45)

**Do:** From a successful Personal Loan run, open a customer who is **ineligible** if present (e.g. high risk / Kavya Desai style case). Point at risk category vs score.

**Say:**

> One common confusion: a medium score like the sixties does **not** by itself mean eligible.  
> Eligibility uses rules such as **maximum allowed risk level** for the product. A customer with **HIGH** risk can fail the product rule even when a value score looks acceptable.  
> Risk bands in seed data are **HIGH / MEDIUM / LOW**. Scoring classes for display are roughly under 40, 40–69, and 70+.  
> Contactability also needs consent — eligibility and compliance are separate gates.

---

## SCENE 8 — Approval + delete + home (10:00)

**Do:**
1. Approve one draft (if UI allows).
2. Show mock send / audit if visible.
3. Show **Back to home**.
4. Optionally **Delete** a campaign → confirm in the modal.

**Say:**

> Human-in-the-loop is non-negotiable for this POC. Approve, then mock send — still no real WhatsApp API.  
> Campaigns can be deleted with an explicit confirm dialog so demos stay tidy. From results you can return home in one click.

---

## SCENE 9 — Close (10:45)

**Do:** Show GitHub repo page or README Quick start.

**Say:**

> To try this yourself: clone **chintanshah9389/RM-AGENTIC-AI**, install Python 3.11+ and Node 20+, seed the database, run the API on 8000 and the web app on 5173 — full steps are in the README.  
> Optional NVIDIA key if you want a live LLM; otherwise the mock provider runs fully offline.  
> Thanks for watching — happy to take questions on agents, tools, or validation.

---

## B-roll / cutaways (optional inserts)

| Clip | Why |
|------|-----|
| API `/docs` Swagger for 3s | Shows real backend |
| SQLite viewer on `customers` / `products` | Proves data is in DB |
| Behind-the-scenes log scrolled slowly | Agent credibility |
| Side-by-side: Personal Loan results vs Gold Loan empty | Strongest “what we solved” moment |

---

## On-screen text overlays (optional in CapCut / Loom)

1. `POC · Synthetic data · No real WhatsApp`
2. `LangGraph + LangChain tools`
3. `Validate LLM → catalogue wins`
4. `Gold Loan missing → No data found (no PL fallback)`
5. `Human approval before mock send`

---

## Checklist after recording

- [ ] Face/name intro optional; product story clear in first 45s  
- [ ] Happy path completed end-to-end  
- [ ] Behind-the-scenes tools named out loud  
- [ ] Gold/Car Loan empty-state shown  
- [ ] Eligibility vs score explained once  
- [ ] Disclaimer said twice (synthetic + no real send)  
- [ ] Repo URL said and/or shown  

---

## If you need a shorter 5-minute cut

Keep only: Scene 0 → 3 (login, skip long customers) → 4 (happy path) → 6 (Gold Loan) → 9 (close).  
Drop deep agent list; say “nine governed steps with tools and validators” once.
