"""Avatar settings. Separate from Farnaz Brain."""
from __future__ import annotations

import json
from pathlib import Path

from ..config import STATE_DIR

PATH = STATE_DIR / "avatar.json"
DEFAULTS = {
    "volume": 0.85,
    "muted": False,
    "hidden": False,
    "lang": "auto",
    "x": 24,
    "y": 72,
    "minimized": False,
    "portrait_path": None,
    "allow_browser_stt": True,
}


def load() -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not PATH.exists():
        return dict(DEFAULTS)
    try:
        data = json.loads(PATH.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULTS)
    out = dict(DEFAULTS)
    out.update({k: data[k] for k in DEFAULTS if k in data})
    return out


def save(data: dict) -> dict:
    cur = load()
    cur.update({k: data[k] for k in DEFAULTS if k in data})
    PATH.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    return cur
