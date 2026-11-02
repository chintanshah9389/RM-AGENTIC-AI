"""Decode latest (or given) CDP Page.captureScreenshot JSON into a PNG."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

LOG_DIR = Path(r"C:\Users\9389c\.cursor\browser-logs")
FRAMES = Path(__file__).resolve().parent / "frames"


def latest_capture() -> Path:
    files = sorted(LOG_DIR.glob("cdp-response-Page.captureScreenshot-*.json"))
    if not files:
        raise SystemExit("No CDP screenshot logs found")
    return files[-1]


def save(dest_name: str, src: Path | None = None) -> Path:
    src = src or latest_capture()
    payload = json.loads(src.read_text(encoding="utf-8"))
    b64 = payload.get("data") or (payload.get("result") or {}).get("data")
    if not b64:
        raise SystemExit(f"No image data in {src}")
    FRAMES.mkdir(parents=True, exist_ok=True)
    out = FRAMES / dest_name
    out.write_bytes(base64.b64decode(b64))
    from PIL import Image

    im = Image.open(out)
    print(f"{out.name} {im.size} from {src.name}")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: save_cdp_shot.py <filename.png> [optional-json-path]")
    src = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    save(sys.argv[1], src)
