# RM Agentic AI — Banking CRM POC

Intelligent customer insights. Personalized outreach. Higher conversions — as a **working take-home / demo POC** with synthetic Indian banking data.

> **POC Environment — Synthetic Data only**  
> Scores, recommendations, and offers do **not** represent real lending or credit decisions.  
> No real WhatsApp messages are sent (mock provider only).

**GitHub:** [chintanshah9389/RM-AGENTIC-AI](https://github.com/chintanshah9389/RM-AGENTIC-AI)

### Demo video (walkthrough)

Watch a live UI walkthrough (Personal Loan happy path + Gold Loan empty state, with on-screen captions):

**[docs/demo-video/RM-AGENTIC-AI-demo.mp4](docs/demo-video/RM-AGENTIC-AI-demo.mp4)**

On GitHub: open that path → click the file → **Download** / play in browser.  
Narrated click script (optional): [docs/DEMO_VIDEO_SCRIPT.md](docs/DEMO_VIDEO_SCRIPT.md)

### Architecture (HLD / LLD)

| Doc | Link |
|-----|------|
| **High-Level Design** | [docs/HLD.md](docs/HLD.md) |
| **Low-Level Design** | [docs/LLD.md](docs/LLD.md) |
| Architecture index | [docs/architecture.md](docs/architecture.md) |

---

## What this demo does

A Relationship Manager (RM) types a natural-language request, for example:

> Find high-value customers likely to convert for a Personal Loan this month and prepare personalized WhatsApp messages.

The system then runs a governed multi-agent workflow:

1. **Intent Understanding** — parses product / channel / segment (LangChain agent + catalogue tools)
2. **Customer Retrieval** — searches Customer360 profiles from the DB
3. **Customer Value Scoring** — transparent heuristic score (0–100)
4. **Conversion Propensity** — transparent heuristic score (0–100)
5. **Product Recommendation** — scoped to the requested catalogue category
6. **Eligibility Rules** — income, age, risk, delinquency, etc.
7. **Consent / Compliance** — hard gate for contact
8. **Message Generation** — WhatsApp draft (LLM or mock)
9. **Explainability** — why the customer was selected
10. **Human approval** → mock WhatsApp send → audit trail

If the requested product is **not in the catalogue** (e.g. Gold Loan / Car Loan), the shortlist is empty with **No data found** — the system does **not** silently substitute Personal Loan.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router, Recharts, Lucide |
| Backend API | FastAPI, Uvicorn, Pydantic Settings, SQLAlchemy 2 |
| Auth | JWT (python-jose), demo users with bcrypt passwords |
| Orchestration | LangGraph (default) + Supervisor persistence / approval gate |
| Agents / LLM | LangChain `create_agent` + tools; `mock` (offline) or `nvidia` (optional) |
| Database | SQLite (default local) or PostgreSQL (optional Docker) |
| Messaging | Mock WhatsApp provider (no real sends) |
| Tests | pytest (API), Vitest (web) |

---

## Repository structure

```text
RM-AGENTIC-AI / bussinessNext
├── apps/
│   ├── api/                 # FastAPI backend
│   │   ├── app/             # agents, workflows, services, models, API routes
│   │   ├── scripts/         # seed_database.py, ensure_product_catalogue.py
│   │   └── requirements.txt
│   └── web/                 # React + Vite frontend
│       ├── src/pages/       # Home, Customers, Campaign, Workflow, Results
│       └── package.json
├── docs/                    # Architecture notes
├── infra/                   # Optional Docker Compose (Postgres)
├── data/                    # Optional exported seed JSON
├── .env.example             # Copy to apps/api/.env
├── Makefile                 # Convenience targets
└── README.md
```

---

## What you need to download / install

### Required

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.11+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js** | 20+ (LTS) | [nodejs.org](https://nodejs.org/) |
| **Git** | latest | [git-scm.com](https://git-scm.com/downloads) |

During Python install on Windows, enable **“Add python.exe to PATH”**.

### Optional

| Tool | Why |
|------|-----|
| **NVIDIA API key** | Use a real LLM instead of mock (`LLM_PROVIDER=nvidia`) — [NVIDIA API Catalog](https://build.nvidia.com/) |
| **Docker Desktop** | Run PostgreSQL instead of SQLite |
| **DB Browser for SQLite** | Inspect `agentic_banking_crm.db` tables |
| **Cursor / VS Code SQLite Viewer** | Open `.db` files inside the editor |

---

## Quick start (Windows)

### 1) Clone the repo

```powershell
git clone https://github.com/chintanshah9389/RM-AGENTIC-AI.git
cd RM-AGENTIC-AI
```

### 2) Backend API

```powershell
cd apps\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Config (from repo root .env.example)
copy ..\..\.env.example .env

# Create ~5,000 synthetic customers + products + demo users
python scripts\seed_database.py

# Run API (from apps/api, with PYTHONPATH set)
$env:PYTHONPATH="."
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3) Frontend (new terminal)

```powershell
cd apps\web
npm install
npm run dev
```

Web app: [http://127.0.0.1:5173](http://127.0.0.1:5173)

### 4) Login (demo users)

| Role | Email | Password |
|------|-------|----------|
| Relationship Manager | `rm@demo.bank` | `Demo@123` |
| Supervisor | `supervisor@demo.bank` | `Demo@123` |
| Admin | `admin@demo.bank` | `Demo@123` |

---

## Quick start (macOS / Linux)

```bash
git clone https://github.com/chintanshah9389/RM-AGENTIC-AI.git
cd RM-AGENTIC-AI

# API
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../../.env.example .env
python scripts/seed_database.py
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Web (second terminal)
cd apps/web
npm install
npm run dev
```

---

## Environment variables

Copy `.env.example` → `apps/api/.env`.

| Variable | Default | Meaning |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite:///./agentic_banking_crm.db` | Local SQLite file under `apps/api/` |
| `LLM_PROVIDER` | `mock` | `mock` (offline) or `nvidia` |
| `NVIDIA_API_KEY` | empty | Required only for NVIDIA mode |
| `NVIDIA_MODEL` | `nvidia/nemotron-3.5-bolt-e4b` | Model id in NVIDIA catalog |
| `ORCHESTRATOR_ENGINE` | `langgraph` | `langgraph` or `native` |
| `JWT_SECRET` | demo value | Change for any shared/deployed env |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Frontend origins |
| `CUSTOMER_SEED_COUNT` | `5000` | Synthetic customers on seed (via settings) |

### Using NVIDIA LLM (optional)

```env
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=your_key_here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=nvidia/nemotron-3.5-bolt-e4b
```

If NVIDIA fails (missing key, network, model error), agents fall back to mock / deterministic paths so the demo keeps working.

---

## How to try the RM journey

1. Open [http://127.0.0.1:5173](http://127.0.0.1:5173) and sign in as RM.
2. Open **Customer list** — browse profiles (account type + masked account number).
3. Click **Start AI campaign**.
4. Enter a request (or use an example chip), then **Start AI campaign**.
5. A **Behind the scenes** popup shows live agent / tool / LLM activity.
6. When ready, continue to the workflow / shortlist.
7. Open a **cleared** customer → review draft → approve → mock send.

### Example requests

| Request | Expected |
|---------|----------|
| Personal Loan / Home Loan / Credit Card | Shortlist from catalogue products |
| Gold Loan / Car Loan (not in catalogue) | **No data found** — empty shortlist |

### Product catalogue (seeded)

- Personal Loan: Standard, Premium, Salary Advantage  
- Home Loan: Standard, Premium  
- Credit Card: Classic  

Eligibility uses demo rules (income, age 21–65, max risk **MEDIUM**, delinquency, optional salary account, optional min value score).

### Score labels (value / propensity)

| Score | Classification |
|------:|----------------|
| &lt; 40 | LOW |
| 40–69 | MEDIUM |
| ≥ 70 | HIGH |

Customer **risk category** (`LOW` / `MEDIUM` / `HIGH`) is separate seed data used by eligibility.

---

## Useful URLs

| Service | URL |
|---------|-----|
| Frontend | http://127.0.0.1:5173 |
| API Swagger | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/api/v1/health |
| Admin products | http://127.0.0.1:8000/api/v1/admin/products |

---

## Makefile helpers (optional)

From repo root (Windows Git Bash / WSL, or adapt paths):

```bash
make seed      # seed DB
make api       # run API
make web       # run Vite
make test-api  # pytest
make test-web  # vitest
```

---

## Testing

```powershell
# API
cd apps\api
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
pytest -q

# Web
cd apps\web
npm run test
```

---

## Viewing the database

SQLite file (after seed): `apps/api/agentic_banking_crm.db`

- Do **not** open it as a text file in the editor (binary).
- Use **DB Browser for SQLite**, or a Cursor/VS Code **SQLite Viewer** extension.
- Or query via API / Customer list UI.

Main tables: `customers`, `accounts`, `products`, `campaigns`, `workflow_runs`, `message_drafts`, `audit_events`, …

---

## Architecture notes

- Diagram: `architecture.jpg` / `docs/architecture.md`
- Orchestrator: LangGraph agent graph + supervisor ranking, persistence, human approval
- Intent is grounded on the **live product catalogue** — unavailable products do not fall back to Personal Loan
- Campaign runs can start **asynchronously** so the UI can stream behind-the-scenes activity

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `uvicorn` not found | Activate `.venv` first |
| Port 8000 already in use | Stop the old Python/uvicorn process, then restart |
| Empty customer list | Re-run `python scripts/seed_database.py` from `apps/api` |
| Frontend can’t reach API | Confirm API on `:8000` and CORS in `.env` |
| NVIDIA `OpenAIModelNotFoundError` | Check model id / key, or set `LLM_PROVIDER=mock` |
| PowerShell blocks `Activate.ps1` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

---

## Security / compliance (POC)

- Synthetic customers only  
- Account numbers are **masked**  
- WhatsApp send is **simulated**  
- Audit events recorded for key actions  
- Do not commit real API keys — use `.env` (gitignored)

---

## License / purpose

Built as an **Agentic AI Banking CRM demonstration / take-home POC** for Relationship Manager outreach workflows.
