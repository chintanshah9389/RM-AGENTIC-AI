"""Record a human-like live demo with on-screen explanatory captions + Gold Loan empty state."""

from __future__ import annotations

import random
import shutil
import subprocess
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

BASE = "http://127.0.0.1:5173"
ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "live-raw"
OUT_MP4 = ROOT / "RM-AGENTIC-AI-demo.mp4"
W, H = 1920, 1080

CAPTION_INIT_JS = r"""
(() => {
  if (window.__demoCaptionReady) return;
  window.__demoCaptionReady = true;

  const ensure = () => {
    let bar = document.getElementById('demo-explain-bar');
    if (bar) return bar;
    bar = document.createElement('div');
    bar.id = 'demo-explain-bar';
    bar.style.cssText = [
      'position:fixed','left:0','right:0','bottom:0','z-index:2147483647',
      'background:rgba(15,23,42,0.94)','color:#f8fafc','padding:16px 28px 18px',
      'font:600 22px/1.35 Segoe UI,Arial,sans-serif','border-top:4px solid #2563eb',
      'box-shadow:0 -8px 24px rgba(0,0,0,.25)','pointer-events:none',
      'min-height:72px','display:flex','align-items:center'
    ].join(';');
    const label = document.createElement('div');
    label.id = 'demo-explain-text';
    label.textContent = 'RM Agentic AI demo';
    bar.appendChild(label);
    document.documentElement.appendChild(bar);
    return bar;
  };

  window.__setDemoCaption = (text) => {
    const bar = ensure();
    const el = document.getElementById('demo-explain-text');
    if (el) el.textContent = text || '';
    bar.style.display = text ? 'flex' : 'none';
  };

  const mo = new MutationObserver(() => ensure());
  const start = () => {
    ensure();
    mo.observe(document.documentElement, { childList: true, subtree: true });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
"""


def pause(page: Page, a: float = 0.4, b: float = 0.9) -> None:
    page.wait_for_timeout(int(random.uniform(a, b) * 1000))


def explain(page: Page, text: str, hold: float = 2.2) -> None:
    """Show narration caption and hold so viewers can read it."""
    try:
        page.evaluate("(t) => window.__setDemoCaption && window.__setDemoCaption(t)", text)
    except Exception:
        # SPA remount / navigation race — reinject then set
        page.evaluate(CAPTION_INIT_JS)
        page.evaluate("(t) => window.__setDemoCaption && window.__setDemoCaption(t)", text)
    page.wait_for_timeout(int(hold * 1000))


def human_click(page: Page, locator) -> None:
    target = locator.first if hasattr(locator, "first") else locator
    target.scroll_into_view_if_needed()
    pause(page, 0.25, 0.55)
    box = target.bounding_box()
    if box:
        x = box["x"] + box["width"] * random.uniform(0.35, 0.65)
        y = box["y"] + box["height"] * random.uniform(0.35, 0.65)
        page.mouse.move(x, y, steps=random.randint(8, 18))
        pause(page, 0.12, 0.28)
        page.mouse.click(x, y)
    else:
        target.click()
    pause(page, 0.35, 0.7)


def human_type(page: Page, locator, text: str, clear: bool = True) -> None:
    human_click(page, locator)
    if clear:
        page.keyboard.press("Control+A")
        pause(page, 0.1, 0.2)
        page.keyboard.press("Backspace")
        pause(page, 0.15, 0.3)
    for ch in text:
        page.keyboard.type(ch, delay=random.randint(50, 110))
        if ch in " .,":
            pause(page, 0.1, 0.22)
    pause(page, 0.35, 0.7)


def wait_enabled(locator, timeout_ms: int = 180_000) -> None:
    locator.wait_for(state="visible", timeout=timeout_ms)
    page = locator.page
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        if locator.is_enabled():
            return
        page.wait_for_timeout(400)
    raise TimeoutError("control stayed disabled")


def main() -> None:
    if RAW_DIR.exists():
        shutil.rmtree(RAW_DIR)
    RAW_DIR.mkdir(parents=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            slow_mo=65,
            args=["--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=1,
            record_video_dir=str(RAW_DIR),
            record_video_size={"width": W, "height": H},
        )
        context.add_init_script(CAPTION_INIT_JS)
        page = context.new_page()
        t0 = time.time()

        # 1) Login
        page.goto(f"{BASE}/login", wait_until="networkidle")
        explain(
            page,
            "POC demo · synthetic banking data only. RM signs in with demo credentials.",
            2.8,
        )
        human_type(page, page.get_by_label("Work email"), "rm@demo.bank")
        human_type(page, page.get_by_label("Password"), "Demo@123")
        explain(page, "Quick demo login as Relationship Manager (password Demo@123).", 2.0)
        human_click(page, page.get_by_role("button", name="Login as RM"))
        pause(page, 0.4, 0.7)
        human_click(page, page.get_by_role("button", name="Continue to Home"))
        page.get_by_role("heading", name="Welcome, Demo Relationship Manager").wait_for(timeout=30_000)
        explain(
            page,
            "Home dashboard: 5,000 synthetic customers. Next we browse profiles, then start an AI campaign.",
            3.0,
        )

        # 2) Customers
        human_click(page, page.get_by_role("link", name="Customer list"))
        page.wait_for_url("**/customers", timeout=20_000)
        explain(
            page,
            "Customer list = Customer360 browse. Scoring and WhatsApp drafting happen inside a campaign.",
            3.0,
        )
        page.mouse.wheel(0, 420)
        pause(page, 1.4, 2.0)

        # 3) Create Personal Loan campaign
        human_click(page, page.get_by_role("navigation").get_by_role("link", name="Start AI campaign"))
        page.wait_for_url("**/campaigns/new", timeout=20_000)
        explain(
            page,
            "HAPPY PATH: create a Personal Loan campaign in plain English — agents resolve product from the catalogue.",
            3.2,
        )

        human_type(page, page.get_by_label("Campaign name"), "Personal Loan Happy Path Demo")
        explain(page, "Use the Personal Loan example, then refine the natural-language request.", 2.2)
        human_click(page, page.get_by_role("button", name="Personal Loan example"))
        pause(page, 0.7, 1.0)
        human_type(
            page,
            page.get_by_label("What should the AI do?"),
            "Find high-value customers likely to convert for a Personal Loan this month "
            "and prepare personalized WhatsApp messages.",
        )
        explain(page, "Optional score filters: how many customers + minimum value/conversion scores.", 2.4)
        human_type(page, page.get_by_label("How many customers?"), "10")
        human_type(page, page.get_by_label("Min. value score"), "50")
        human_type(page, page.get_by_label("Min. conversion score"), "40")
        pause(page, 0.7, 1.1)

        # 4) Agents processing
        explain(
            page,
            "Start AI campaign → behind-the-scenes modal shows LangGraph agents, tools, and LLM activity live.",
            2.8,
        )
        human_click(page, page.get_by_role("button", name="Start AI campaign"))
        page.get_by_role("heading", name="AI campaign setup").wait_for(timeout=30_000)
        explain(
            page,
            "Intent agent calls list_active_products. PERSONAL_LOAN must match the catalogue — no silent substitute.",
            3.2,
        )

        continue_btn = page.get_by_role("button", name="Continue to shortlist preview")
        captions_mid = [
            "Retrieval agent searches Customer360 via search_customers (DB is source of truth).",
            "Value + propensity scoring (0–100 heuristics). Then product recommendation for Personal Loan.",
            "Eligibility rules + consent/compliance hard gates. Only cleared contacts get WhatsApp drafts.",
            "Message agent drafts WhatsApp with STOP + eligibility disclaimer. Waiting for human approval…",
        ]
        for i, cap in enumerate(captions_mid):
            explain(page, cap, 2.6)
            page.mouse.move(
                random.randint(900, 1400),
                random.randint(420, 780),
                steps=random.randint(6, 12),
            )
            page.mouse.wheel(0, random.randint(60, 140))
            if continue_btn.count() and continue_btn.is_enabled():
                # keep reading a bit even after ready
                if i >= 2:
                    break
        wait_enabled(continue_btn, 180_000)
        explain(page, "Setup complete. Continue to the Personal Loan shortlist for RM review.", 2.8)
        human_click(page, continue_btn)

        page.get_by_role("heading", name="Customer shortlist").wait_for(timeout=60_000)
        explain(
            page,
            "Shortlist for PERSONAL LOAN: cleared customers can be reviewed; blocked ones show why.",
            3.2,
        )
        page.mouse.wheel(0, 280)
        pause(page, 1.2, 1.8)

        # 5) Blocked explanation
        why = page.get_by_role("link", name="View why blocked")
        if why.count() > 0:
            explain(
                page,
                "Open a blocked customer: a good score is not enough — eligibility/compliance can still block contact.",
                2.8,
            )
            human_click(page, why.first)
            pause(page, 1.4, 2.0)
            page.mouse.wheel(0, 420)
            explain(
                page,
                "Explainability: risk, delinquency, income, consent. Banking demos must show the reason.",
                3.0,
            )
            back = page.get_by_role("link", name="Back to shortlist")
            if back.count():
                human_click(page, back)
            else:
                page.go_back()
            page.get_by_role("heading", name="Customer shortlist").wait_for(timeout=30_000)
            pause(page, 0.7, 1.1)

        # 6) Happy review + approve + mock send
        review = page.get_by_role("link", name="Review & approve")
        if review.count() == 0:
            raise RuntimeError("No Review & approve link — happy path failed")
        explain(page, "Happy path: open a CLEARED customer to review scores, product, and WhatsApp draft.", 2.8)
        human_click(page, review.first)
        pause(page, 1.3, 1.8)

        explain(page, "Review profile, accounts, value score, conversion chance, and suggested Personal Loan.", 2.6)
        for dy in (300, 360, 400, 420, 380):
            page.mouse.wheel(0, dy)
            pause(page, 1.1, 1.6)

        draft = page.get_by_role("heading", name="WhatsApp message draft")
        draft.scroll_into_view_if_needed()
        explain(
            page,
            "Validated draft includes product, STOP opt-out, eligibility disclaimer, and dummy-data notice.",
            3.0,
        )

        explain(page, "Human-in-the-loop: Approve message — agents never auto-send.", 2.4)
        human_click(page, page.get_by_role("button", name="Approve message"))
        pause(page, 1.1, 1.6)
        send = page.get_by_role("button", name="Send mock WhatsApp")
        wait_enabled(send, 30_000)
        explain(page, "Send mock WhatsApp — simulated only. No real customer message leaves this POC.", 2.8)
        human_click(page, send)
        pause(page, 2.2, 2.8)

        # 7) Gold Loan empty state (governance)
        explain(
            page,
            "CONTRAST: request Gold Loan (not in catalogue). System must show No data found — not swap Personal Loan.",
            3.2,
        )
        page.goto(f"{BASE}/campaigns/new", wait_until="networkidle")
        explain(page, "Click Unavailable product example → Gold Loan request.", 2.4)
        human_click(page, page.get_by_role("button", name="Unavailable product example"))
        pause(page, 0.8, 1.2)
        explain(page, "Start campaign and watch validators reject the missing product.", 2.4)
        human_click(page, page.get_by_role("button", name="Start AI campaign"))
        page.get_by_role("heading", name="AI campaign setup").wait_for(timeout=30_000)
        explain(
            page,
            "Live log: not_in_catalogue:GOLD_LOAN · tool list_active_products · product stays UNRESOLVED.",
            3.4,
        )
        gold_continue = page.get_by_role("button", name="Continue to shortlist preview")
        wait_enabled(gold_continue, 120_000)
        pause(page, 1.5, 2.2)
        human_click(page, gold_continue)
        page.get_by_role("heading", name="Customer shortlist").wait_for(timeout=60_000)
        explain(
            page,
            "EMPTY STATE: No data found for Gold Loan. Available catalogue: CREDIT_CARD, HOME_LOAN, PERSONAL_LOAN.",
            4.0,
        )
        pause(page, 2.0, 2.6)

        explain(
            page,
            "Demo complete: Personal Loan happy path + governed empty state for missing products. Synthetic data only.",
            3.5,
        )

        elapsed = time.time() - t0
        print(f"recorded interaction ~{elapsed:.1f}s")
        context.close()
        browser.close()

    videos = list(RAW_DIR.glob("*.webm"))
    if not videos:
        raise RuntimeError("No Playwright video produced")
    raw = max(videos, key=lambda p: p.stat().st_size)
    print(f"raw video: {raw} ({raw.stat().st_size} bytes)")

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg:
        candidates = list(Path.home().glob("AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/**/ffmpeg.exe"))
        if candidates:
            ffmpeg = str(candidates[0])
            ffprobe = str(candidates[0].parent / "ffprobe.exe")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found")
    if not ffprobe:
        ffprobe = "ffprobe"

    duration = float(
        subprocess.check_output(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(raw),
            ],
            text=True,
        ).strip()
    )
    print(f"raw duration: {duration:.1f}s (~{duration/60:.1f} min)")

    # No duration cap — keep natural pacing
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(raw),
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(OUT_MP4),
    ]
    subprocess.run(cmd, check=True)
    print(f"Wrote {OUT_MP4} ({OUT_MP4.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
