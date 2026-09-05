"""One job per plugin project. Recover stale locks."""
from __future__ import annotations

import json
import time
from pathlib import Path

from ..config import STATE_DIR

STORE = STATE_DIR / "factory_project_locks.json"
STALE_SEC = 30 * 60
MAX_REPAIR_ATTEMPTS = 3


def _load() -> dict:
    if not STORE.exists():
        return {}
    try:
        return json.loads(STORE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(data), encoding="utf-8")


def acquire(project: str, job_id: str) -> dict:
    data = _load()
    now = time.time()
    cur = data.get(project)
    if cur and now - cur.get("ts", 0) < STALE_SEC and cur.get("job_id") != job_id:
        return {"ok": False, "error": "locked", "by": cur}
    data[project] = {"job_id": job_id, "ts": now, "repairs": cur.get("repairs", 0) if cur else 0}
    _save(data)
    return {"ok": True, "project": project, "job_id": job_id}


def release(project: str, job_id: str) -> dict:
    data = _load()
    cur = data.get(project)
    if cur and cur.get("job_id") == job_id:
        data.pop(project, None)
        _save(data)
    return {"ok": True}


def repair_tick(project: str) -> dict:
    data = _load()
    cur = data.get(project) or {"repairs": 0}
    n = int(cur.get("repairs", 0)) + 1
    cur["repairs"] = n
    data[project] = cur
    _save(data)
    if n > MAX_REPAIR_ATTEMPTS:
        return {"ok": False, "stop": True, "repairs": n, "error": "MAX_REPAIR_ATTEMPTS"}
    return {"ok": True, "repairs": n}
