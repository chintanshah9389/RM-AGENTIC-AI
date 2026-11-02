"""Capture a detailed Personal Loan happy-path demo at 1920x1080."""

from __future__ import annotations

import re
import time
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

BASE = "http://127.0.0.1:5173"
FRAMES = Path(__file__).resolve().parent / "frames"
W, H = 1920, 1080


def shot(page: Page, name: str) -> None:
    path = FRAMES / name
    page.screenshot(path=str(path), full_page=False)
    print(f"saved {path.name}")


def wait_enabled(locator, timeout_ms: int = 180_000) -> None:
    locator.wait_for(state="visible", timeout=timeout_ms)
    page = locator.page
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        if locator.is_enabled():
            return
        page.wait_for_timeout(400)
    raise TimeoutError("control stayed disabled")


def campaign_id_from_url(url: str) -> str | None:
    m = re.search(r"/campaigns/([0-9a-fA-F-]{36})", url)
    return m.group(1) if m else None


def goto_results(page: Page, cid: str | None = None) -> None:
    cid = cid or campaign_id_from_url(page.url)
    if not cid:
        raise RuntimeError(f"No campaign id in {page.url}")
    page.goto(f"{BASE}/campaigns/{cid}/results", wait_until="networkidle")
    page.get_by_role("heading", name="Customer shortlist").wait_for(timeout=60_000)
    page.wait_for_timeout(1200)


def wait_text(page: Page, pattern: str, timeout_ms: int = 120_000) -> None:
    page.get_by_text(re.compile(pattern, re.I)).first.wait_for(timeout=timeout_ms)


def main() -> None:
    FRAMES.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1)
        page = context.new_page()

        # --- Login ---
        page.goto(f"{BASE}/login", wait_until="networkidle")
        page.get_by_label("Work email").fill("rm@demo.bank")
        page.get_by_label("Password").fill("Demo@123")
        page.wait_for_timeout(500)
        shot(page, "hp-01-login.png")

        page.get_by_role("button", name="Login as RM").click()
        page.wait_for_timeout(250)
        page.get_by_role("button", name="Continue to Home").click()
        page.get_by_role("heading", name="Welcome, Demo Relationship Manager").wait_for(timeout=30_000)
        page.wait_for_timeout(1200)
        shot(page, "hp-02-home.png")

        # --- Customers ---
        page.goto(f"{BASE}/customers", wait_until="networkidle")
        page.wait_for_timeout(2500)
        shot(page, "hp-03-customers-top.png")
        page.evaluate("window.scrollTo(0, 420)")
        page.wait_for_timeout(700)
        shot(page, "hp-04-customers-table.png")

        # --- Create Personal Loan campaign (explicit example + low score gates) ---
        page.goto(f"{BASE}/campaigns/new", wait_until="networkidle")
        page.get_by_label("Campaign name").fill("Personal Loan Happy Path Demo")
        page.get_by_role("button", name="Personal Loan example").click()
        page.wait_for_timeout(400)
        # Reinforce exact request text
        page.get_by_label("What should the AI do?").fill(
            "Find high-value customers likely to convert for a Personal Loan this month "
            "and prepare personalized WhatsApp messages."
        )
        page.get_by_label("How many customers?").fill("10")
        page.get_by_label("Min. value score").fill("50")
        page.get_by_label("Min. conversion score").fill("40")
        page.wait_for_timeout(600)
        shot(page, "hp-05-create-personal-loan.png")
        page.evaluate("window.scrollTo(0, 500)")
        page.wait_for_timeout(500)
        shot(page, "hp-06-create-filters.png")

        page.get_by_role("button", name="Start AI campaign").click()
        page.get_by_role("heading", name="AI campaign setup").wait_for(timeout=30_000)
        page.wait_for_timeout(2000)
        shot(page, "hp-07-modal-start.png")

        # Wait until Personal Loan is resolved in live log (not AUTO / unresolved)
        wait_text(page, r"PERSONAL[_ ]?LOAN|Personal Loan", timeout_ms=90_000)
        page.wait_for_timeout(800)
        shot(page, "hp-08-modal-intent-personal-loan.png")

        # Capture mid-pipeline frames while agents run
        for i, delay in enumerate([4, 6, 8, 10], start=9):
            page.wait_for_timeout(delay * 1000)
            shot(page, f"hp-{i:02d}-modal-agents.png")

        continue_btn = page.get_by_role("button", name="Continue to shortlist preview")
        if continue_btn.count() == 0:
            continue_btn = page.get_by_role("button", name="Open live preview")
        wait_enabled(continue_btn, 180_000)
        # Prefer seeing drafts / HumanApproval before leaving
        try:
            wait_text(page, r"HumanApproval|message draft|Setup complete", timeout_ms=30_000)
        except Exception:
            pass
        page.wait_for_timeout(1000)
        shot(page, "hp-13-modal-complete.png")

        with page.expect_navigation(timeout=60_000):
            continue_btn.click()
        page.wait_for_timeout(1200)
        cid = campaign_id_from_url(page.url)
        if "/results" not in page.url:
            goto_results(page, cid)
        else:
            page.get_by_role("heading", name="Customer shortlist").wait_for(timeout=60_000)
            page.wait_for_timeout(1500)

        # Must be Personal Loan shortlist with customers
        body = page.locator("body").inner_text()
        if "No data found" in body or "PERSONAL" not in body.upper():
            # one retry with even looser filters
            print("WARN: shortlist empty or not Personal Loan — retrying campaign")
            page.goto(f"{BASE}/campaigns/new", wait_until="networkidle")
            page.get_by_label("Campaign name").fill("Personal Loan Happy Path Retry")
            page.get_by_role("button", name="Personal Loan example").click()
            page.get_by_label("What should the AI do?").fill(
                "Find Premium and high-value customers for Personal Loan WhatsApp outreach this month."
            )
            page.get_by_label("How many customers?").fill("12")
            page.get_by_label("Min. value score").fill("40")
            page.get_by_label("Min. conversion score").fill("30")
            page.get_by_role("button", name="Start AI campaign").click()
            page.get_by_role("heading", name="AI campaign setup").wait_for(timeout=30_000)
            wait_text(page, r"PERSONAL[_ ]?LOAN|Personal Loan", timeout_ms=90_000)
            cont = page.get_by_role("button", name="Continue to shortlist preview")
            wait_enabled(cont, 180_000)
            with page.expect_navigation(timeout=60_000):
                cont.click()
            page.wait_for_timeout(1200)
            cid = campaign_id_from_url(page.url)
            if "/results" not in page.url:
                goto_results(page, cid)
            page.wait_for_timeout(1500)
            body = page.locator("body").inner_text()
            if "No data found" in body:
                raise RuntimeError("Personal Loan shortlist still empty after retry")

        shot(page, "hp-14-shortlist.png")
        expect(page.get_by_text(re.compile(r"PERSONAL", re.I)).first).to_be_visible()
        page.wait_for_timeout(800)
        shot(page, "hp-15-shortlist-closeup.png")

        # Blocked explanation (if present)
        why = page.get_by_role("link", name="View why blocked")
        if why.count() > 0:
            why.first.click()
            page.wait_for_timeout(2000)
            shot(page, "hp-16-blocked-top.png")
            page.evaluate("window.scrollTo(0, 450)")
            page.wait_for_timeout(600)
            shot(page, "hp-17-blocked-eligibility.png")
            back = page.get_by_role("link", name="Back to shortlist")
            if back.count():
                back.click()
            else:
                page.go_back()
            page.wait_for_timeout(1500)
        else:
            shot(page, "hp-16-blocked-top.png")
            shot(page, "hp-17-blocked-eligibility.png")

        # Happy review & approve
        review = page.get_by_role("link", name="Review & approve")
        if review.count() == 0:
            raise RuntimeError("No cleared customer with Review & approve — cannot film happy path")
        review.first.click()
        page.wait_for_timeout(2200)
        shot(page, "hp-18-review-top.png")

        page.evaluate("window.scrollTo(0, 350)")
        page.wait_for_timeout(600)
        shot(page, "hp-19-profile-accounts.png")

        page.evaluate("window.scrollTo(0, 700)")
        page.wait_for_timeout(600)
        shot(page, "hp-20-value-score.png")

        page.evaluate("window.scrollTo(0, 1050)")
        page.wait_for_timeout(600)
        shot(page, "hp-21-propensity-product.png")

        page.evaluate("window.scrollTo(0, 1450)")
        page.wait_for_timeout(600)
        shot(page, "hp-22-eligibility-compliance.png")

        draft = page.get_by_role("heading", name="WhatsApp message draft")
        draft.scroll_into_view_if_needed()
        page.wait_for_timeout(700)
        shot(page, "hp-23-whatsapp-draft.png")

        page.get_by_role("button", name="Approve message").click()
        page.wait_for_timeout(1500)
        shot(page, "hp-24-approved.png")

        send = page.get_by_role("button", name="Send mock WhatsApp")
        wait_enabled(send, 30_000)
        send.click()
        page.wait_for_timeout(2000)
        shot(page, "hp-25-mock-send-done.png")

        # Optional short contrast: Gold Loan governance (keep brief)
        page.goto(f"{BASE}/campaigns/new", wait_until="networkidle")
        page.get_by_role("button", name="Unavailable product example").click()
        page.wait_for_timeout(500)
        shot(page, "hp-26-gold-request.png")
        page.get_by_role("button", name="Start AI campaign").click()
        page.get_by_role("heading", name="AI campaign setup").wait_for(timeout=30_000)
        wait_text(page, r"not_in_catalogue|No data found for Gold Loan|GOLD_LOAN", timeout_ms=90_000)
        page.wait_for_timeout(800)
        shot(page, "hp-27-gold-validation.png")
        cont = page.get_by_role("button", name="Continue to shortlist preview")
        wait_enabled(cont, 120_000)
        with page.expect_navigation(timeout=60_000):
            cont.click()
        page.wait_for_timeout(1000)
        if "/results" not in page.url:
            goto_results(page, campaign_id_from_url(page.url))
        page.wait_for_timeout(1200)
        shot(page, "hp-28-gold-no-data.png")

        browser.close()
        print("capture complete")


if __name__ == "__main__":
    main()
