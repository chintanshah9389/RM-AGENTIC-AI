import httpx

base = "http://127.0.0.1:8000/api/v1"
c = httpx.Client(timeout=60.0)

r = c.post(f"{base}/auth/login", json={"email": "rm@demo.bank", "password": "Demo@123"})
print("login", r.status_code)
r.raise_for_status()
token = r.json()["data"]["access_token"]
h = {"Authorization": f"Bearer {token}"}

r = c.post(
    f"{base}/campaigns",
    headers=h,
    json={
        "name": "E2E Personal Loan",
        "natural_language_request": (
            "Find high-value customers likely to convert for a Personal Loan this month "
            "and prepare personalized WhatsApp messages."
        ),
        "max_customers": 10,
        "min_value_score": 60,
        "min_propensity_score": 50,
    },
)
print("create", r.status_code)
r.raise_for_status()
campaign_id = r.json()["data"]["id"]

r = c.post(f"{base}/campaigns/{campaign_id}/run?wait=true", headers=h)
print("run", r.status_code)
r.raise_for_status()
wf = r.json()["data"]["workflow"]
print("workflow", wf["status"], wf["id"])

r = c.get(f"{base}/campaigns/{campaign_id}/results", headers=h)
r.raise_for_status()
results = r.json()["data"]["results"]
print("results", len(results))
for row in results[:8]:
    print(
        row.get("customerName"),
        row.get("scenarioTag"),
        row.get("compliance"),
        row.get("messageStatus"),
        row.get("contactAllowed"),
    )

target = next((x for x in results if x.get("messageId") and x.get("contactAllowed")), None)
assert target, "No approvable message found"
msg_id = target["messageId"]
print("approving", target["customerName"], msg_id)

r = c.post(f"{base}/messages/{msg_id}/approve", headers=h)
print("approve", r.status_code, r.json().get("success"))
r.raise_for_status()

r = c.post(f"{base}/messages/{msg_id}/simulate-send", headers=h)
print("send", r.status_code)
r.raise_for_status()
print(r.json()["data"]["disclaimer"])

blocked = next((x for x in results if x.get("compliance") == "BLOCKED"), None)
if blocked:
    print("blocked sample", blocked["customerName"], blocked.get("scenarioTag"))

r = c.get(f"{base}/audit-events", headers=h, params={"campaign_id": campaign_id})
r.raise_for_status()
print("audit events", len(r.json()["data"]))
print("E2E OK")
