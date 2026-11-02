"""Build a detailed captioned 1920x1080 demo MP4 (~8–10 minutes)."""

from __future__ import annotations

import shutil
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FRAMES = ROOT / "frames"
OUT_DIR = ROOT / "render"
OUT_MP4 = ROOT / "RM-AGENTIC-AI-demo.mp4"
W, H = 1920, 1080
CAPTION_H = 140
PAD = (241, 245, 249)

# Detailed Personal Loan happy path first; Gold Loan contrast only at the end.
# Target runtime ~8–10 minutes.
SCENES: list[tuple[str, float, str]] = [
    (
        "hp-01-login.png",
        18,
        "RM Agentic AI — Banking CRM POC (1920×1080). Synthetic data only. Login: rm@demo.bank / Demo@123.",
    ),
    (
        "hp-02-home.png",
        20,
        "Home dashboard for the Relationship Manager. 5,000 synthetic customers. Goal: run a governed AI campaign.",
    ),
    (
        "hp-03-customers-top.png",
        16,
        "Customer list: browse Customer360 anytime. Campaign wizard shows the 5-step RM journey.",
    ),
    (
        "hp-04-customers-table.png",
        18,
        "Profiles include segment, income, risk, and accounts. Scoring + WhatsApp drafting happen inside a campaign.",
    ),
    (
        "hp-05-create-personal-loan.png",
        24,
        "HAPPY PATH: create campaign for Personal Loan + WhatsApp in plain English. Agents + catalogue decide product/channel.",
    ),
    (
        "hp-06-create-filters.png",
        18,
        "Optional filters: max customers and minimum value/conversion scores. Then Start AI campaign.",
    ),
    (
        "hp-07-modal-start.png",
        20,
        "Behind-the-scenes popup opens. LangGraph supervisor boots the multi-agent pipeline — live telemetry for the RM.",
    ),
    (
        "hp-08-modal-intent-personal-loan.png",
        26,
        "Intent agent + tool list_active_products. Product resolves to PERSONAL_LOAN (catalogue match). No silent substitute.",
    ),
    (
        "hp-09-modal-agents.png",
        22,
        "Retrieval agent calls search_customers on the DB. Candidates are real Customer360 rows — not LLM inventions.",
    ),
    (
        "hp-10-modal-agents.png",
        22,
        "Scoring agents: customer-value score and conversion propensity (transparent heuristics 0–100 for the POC).",
    ),
    (
        "hp-11-modal-agents.png",
        22,
        "Recommendation scoped to Personal Loan. Eligibility rules + consent/compliance hard gates run next.",
    ),
    (
        "hp-12-modal-agents.png",
        22,
        "Message agent uses get_message_context, then drafts WhatsApp with STOP + eligibility disclaimer validation.",
    ),
    (
        "hp-13-modal-complete.png",
        20,
        "Setup complete — 11 steps done. Human approval is required before any mock send. Continue to shortlist.",
    ),
    (
        "hp-14-shortlist.png",
        24,
        "Customer shortlist for PERSONAL LOAN. Cleared contacts show Review & approve. Blocked contacts show why.",
    ),
    (
        "hp-15-shortlist-closeup.png",
        20,
        "Read scores, eligibility, and contact permission. This is the RM decision surface — not auto-send.",
    ),
    (
        "hp-16-blocked-top.png",
        20,
        "Open a blocked customer: high score alone is not enough. Eligibility/compliance can still block outreach.",
    ),
    (
        "hp-17-blocked-eligibility.png",
        22,
        "Explainability: risk band, delinquency, income, consent. Banking demos must show WHY someone was blocked.",
    ),
    (
        "hp-18-review-top.png",
        20,
        "Happy path continues: open a CLEARED customer. Step 5 — Approve & send. Demo scores are not real lending.",
    ),
    (
        "hp-19-profile-accounts.png",
        20,
        "Customer profile + masked accounts (type/number). RM verifies context before trusting the AI draft.",
    ),
    (
        "hp-20-value-score.png",
        20,
        "Customer value score with HIGH/MEDIUM/LOW band. Weighted heuristic — explainable to an RM stakeholder.",
    ),
    (
        "hp-21-propensity-product.png",
        22,
        "Conversion chance + suggested Personal Loan product with rationale, indicative amount, and rate (demo only).",
    ),
    (
        "hp-22-eligibility-compliance.png",
        22,
        "Eligibility checks PASSED + marketing/WhatsApp consent. Both gates must clear before contact is allowed.",
    ),
    (
        "hp-23-whatsapp-draft.png",
        24,
        "Validated WhatsApp draft: product mention, STOP opt-out, eligibility disclaimer, dummy-data notice.",
    ),
    (
        "hp-24-approved.png",
        18,
        "RM clicks Approve message. Human-in-the-loop unlocks the next action — agents never auto-send.",
    ),
    (
        "hp-25-mock-send-done.png",
        22,
        "Send mock WhatsApp — no real WhatsApp API. Status becomes Mock send done. Audit-friendly demo path.",
    ),
    (
        "hp-26-gold-request.png",
        16,
        "Contrast (short): ask for Gold Loan, which is NOT in the catalogue — governance check.",
    ),
    (
        "hp-27-gold-validation.png",
        18,
        "Validators win: not_in_catalogue:GOLD_LOAN. System must NOT silently swap to Personal Loan.",
    ),
    (
        "hp-28-gold-no-data.png",
        18,
        "No data found for Gold Loan. Happy path was Personal Loan end-to-end; this shows product governance.",
    ),
]


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in (
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ):
        path = Path(name)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def title_card() -> Image.Image:
    img = Image.new("RGB", (W, H), (15, 23, 42))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 14), fill=(37, 99, 235))
    draw.rectangle((0, H - 14, W, H), fill=(37, 99, 235))
    draw.text((120, 240), "RM Agentic AI", fill=(248, 250, 252), font=font(68))
    draw.text((120, 340), "Personal Loan — Full Happy Path Demo", fill=(147, 197, 253), font=font(36))
    y = 440
    for line in [
        "Detailed walkthrough: Intent → Tools → Retrieval → Scores → Eligibility",
        "→ Compliance → WhatsApp draft → Human approve → Mock send",
        "",
        "Captions = narration   ·   Synthetic POC data only   ·   1920×1080",
        "GitHub: chintanshah9389/RM-AGENTIC-AI",
    ]:
        draw.text((120, y), line, fill=(203, 213, 225), font=font(28))
        y += 48
    return img


def end_card() -> Image.Image:
    img = Image.new("RGB", (W, H), (15, 23, 42))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 14), fill=(22, 163, 74))
    draw.text((120, 300), "Thanks for watching", fill=(248, 250, 252), font=font(58))
    y = 420
    for line in [
        "Happy path: Personal Loan campaign completed with human approval",
        "Clone · seed DB · API :8000 · web :5173",
        "Login: rm@demo.bank / Demo@123   ·   See README for setup",
    ]:
        draw.text((120, y), line, fill=(186, 230, 253), font=font(30))
        y += 54
    return img


def fit_screenshot(path: Path) -> Image.Image:
    src = Image.open(path).convert("RGB")
    if src.size == (W, H):
        return src
    scale = min(W / src.width, H / src.height)
    nw = max(1, int(src.width * scale))
    nh = max(1, int(src.height * scale))
    resized = src.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (W, H), PAD)
    canvas.paste(resized, ((W - nw) // 2, (H - nh) // 2))
    return canvas


def add_caption(shot: Image.Image, caption: str) -> Image.Image:
    out = shot.convert("RGB").copy()
    if out.size != (W, H):
        canvas = Image.new("RGB", (W, H), PAD)
        canvas.paste(out, ((W - out.width) // 2, (H - out.height) // 2))
        out = canvas
    draw = ImageDraw.Draw(out)
    draw.rectangle((0, H - CAPTION_H, W, H), fill=(15, 23, 42))
    draw.rectangle((0, H - CAPTION_H, W, H - CAPTION_H + 4), fill=(37, 99, 235))
    wrapped = textwrap.fill(caption, width=115)
    draw.multiline_text(
        (40, H - CAPTION_H + 28),
        wrapped,
        fill=(248, 250, 252),
        font=font(28),
        spacing=8,
    )
    return out


def save_timed_frames(img: Image.Image, seconds: float, start_idx: int, fps: int = 2) -> int:
    n = max(1, int(round(seconds * fps)))
    for i in range(n):
        img.save(OUT_DIR / f"frame_{start_idx + i:05d}.png")
    return start_idx + n


def main() -> None:
    missing = [name for name, _, _ in SCENES if not (FRAMES / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing frames: {missing}")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    fps = 2
    idx = 0
    idx = save_timed_frames(title_card(), 8, idx, fps)
    total_secs = 8.0
    for name, seconds, caption in SCENES:
        frame = add_caption(fit_screenshot(FRAMES / name), caption)
        idx = save_timed_frames(frame, seconds, idx, fps)
        total_secs += seconds
    idx = save_timed_frames(end_card(), 8, idx, fps)
    total_secs += 8.0

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        candidates = list(Path.home().glob("AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/**/ffmpeg.exe"))
        ffmpeg = str(candidates[0]) if candidates else None
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found")

    cmd = [
        ffmpeg,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(OUT_DIR / "frame_%05d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        "-movflags",
        "+faststart",
        str(OUT_MP4),
    ]
    subprocess.run(cmd, check=True)
    print(f"Wrote {OUT_MP4} ({OUT_MP4.stat().st_size} bytes), ~{total_secs/60:.1f} min, {idx} frames")


if __name__ == "__main__":
    main()
