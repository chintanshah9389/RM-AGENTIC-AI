# Demo script (5–10 min)

## Setup

1. Start API on `:8000`
2. Start web on `:5173`
3. Optional: set `LLM_PROVIDER=nvidia` and `NVIDIA_API_KEY` for live LLM demo
4. Otherwise keep `LLM_PROVIDER=mock`

## Use case 1 — Happy path

1. Login `rm@demo.bank` / `Demo@123`
2. Create AI Campaign with default prompt
3. Show live agent stepper completing
4. Open results → customer tagged **S-A** (Priya Sharma)
5. Show scores, product, eligibility PASS, compliance PASS
6. Edit message → Approve → Simulate Send
7. Show disclaimer: Simulated WhatsApp send. No real customer message was sent.

## Use case 2 — Compliance override

1. Open **S-B** (DNC) or **S-F** (no WhatsApp consent)
2. Show high commercial scores but BLOCKED
3. Prove Approve/Simulate Send disabled / API rejects

## Use case 3 — Product fallback / data quality

1. Open **S-C** (Premium income fail → Standard)
2. And/or **S-E** (incomplete transactions warning)
3. Explain tool-based recommendation + heuristic transparency

## Closing

Mention architecture trade-offs: Mock+NVIDIA LLM abstraction, SQLite POC, compliance > score, human-in-the-loop.
