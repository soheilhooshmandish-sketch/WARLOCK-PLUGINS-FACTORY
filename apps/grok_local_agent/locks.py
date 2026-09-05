"""File locks so two agents do not edit the same path. Never lock apps/local_agent (already forbidden)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .config import PROTECTED_PATHS, STATE_DIR

STORE = STATE_DIR / "locks.json"
STALE = 30 * 60


def _load() -> dict:
    if not STORE.exists():
        return {}
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def acquire(path: str, who: str = "farnaz") -> dict:
    rel = path.replace("\\", "/").lstrip("./")
    if any(rel == g or rel.startswith(g + "/") for g in PROTECTED_PATHS):
        return {"ok": False, "error": "LOCKED path is protected"}
    data = _load()
    now = time.time()
    row = data.get(rel)
    if row and now - float(row.get("at") or 0) < STALE and row.get("who") != who:
        return {"ok": False, "error": "busy", "holder": row}
    data[rel] = {"who": who, "at": now}
    _save(data)
    return {"ok": True, "path": rel, "who": who}


def release(path: str, who: str = "farnaz") -> dict:
    rel = path.replace("\\", "/").lstrip("./")
    data = _load()
    data.pop(rel, None)
    _save(data)
    return {"ok": True, "path": rel}
