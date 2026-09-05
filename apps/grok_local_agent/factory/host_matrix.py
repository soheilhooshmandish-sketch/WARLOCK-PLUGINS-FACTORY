"""Verified host results only. Missing a DAW means NOT_TESTED, never PASS."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from ..config import STATE_DIR

HOSTS = ("pluginval", "FL Studio", "REAPER", "Ableton Live", "Cubase", "Studio One")
STORE = STATE_DIR / "host_matrix.json"


def _empty() -> dict:
    return {
        h: {
            "host": h,
            "result": "NOT_TESTED",
            "host_version": None,
            "plugin_version": None,
            "test_date": None,
            "plugin_hash": None,
            "notes": "not executed",
        }
        for h in HOSTS
    }


def load() -> dict:
    if not STORE.exists():
        return _empty()
    try:
        data = json.loads(STORE.read_text(encoding="utf-8"))
    except Exception:
        return _empty()
    base = _empty()
    base.update(data)
    return base


def save(rows: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def record(host: str, result: str, **meta) -> dict:
    if result not in {"NOT_TESTED", "PASS", "WARNING", "FAIL"}:
        return {"ok": False, "error": "bad result"}
    if host not in HOSTS:
        return {"ok": False, "error": "unknown host"}
    rows = load()
    rows[host] = {
        "host": host,
        "result": result,
        "host_version": meta.get("host_version"),
        "plugin_version": meta.get("plugin_version"),
        "test_date": time.strftime("%Y-%m-%d"),
        "plugin_hash": meta.get("plugin_hash"),
        "notes": meta.get("notes", ""),
    }
    save(rows)
    return {"ok": True, **rows[host]}


def auto_pluginval(vst3: Path | None) -> dict:
    """Run only if pluginval exists AND vst3 exists. Never fake PASS."""
    if not shutil.which("pluginval"):
        return record("pluginval", "NOT_TESTED", notes="pluginval binary missing")
    if not vst3 or not Path(vst3).exists():
        return record("pluginval", "NOT_TESTED", notes="VST3 artifact missing")
    from .pluginval_parse import run
    r = run(vst3)
    return record("pluginval", "PASS" if r.get("ok") else "FAIL", notes=str(r.get("error") or r.get("exit")))


def report() -> dict:
    rows = load()
    claimed = [h for h, v in rows.items() if v["result"] == "PASS"]
    return {
        "ok": False,
        "hosts": rows,
        "pass": claimed,
        "note": "PASS only after a real host run. DAWs are NOT_TESTED.",
    }
