"""Action log. Real history only. Never log secrets."""
from __future__ import annotations

import json
import time

from .checkpoint import _conn

DENY = ("password", "api_key", "secret", "token", "ssh-rsa")


def record(op: str, detail: str = "", ok: bool = True) -> None:
    text = (detail or "")[:240]
    low = text.lower()
    if any(w in low for w in DENY):
        text = "[redacted]"
    cx = _conn()
    cx.execute(
        "CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, op TEXT, ok INT, detail TEXT)"
    )
    cx.execute(
        "INSERT INTO actions(ts, op, ok, detail) VALUES (?,?,?,?)",
        (time.time(), op[:40], 1 if ok else 0, text),
    )
    cx.commit()
    cx.close()


def last(n: int = 20) -> list[dict]:
    cx = _conn()
    cx.execute(
        "CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, op TEXT, ok INT, detail TEXT)"
    )
    rows = cx.execute(
        "SELECT ts, op, ok, detail FROM actions ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()
    cx.close()
    out = []
    for ts, op, ok, detail in rows:
        out.append({
            "ts": ts,
            "when": time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)),
            "op": op,
            "ok": bool(ok),
            "detail": detail,
        })
    return out
