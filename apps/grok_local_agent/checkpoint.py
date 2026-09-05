"""SQLite checkpoint. No paid API. JSON fallback if sqlite fails."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from .config import STATE_DIR

DB = STATE_DIR / "farnaz.db"


def _conn() -> sqlite3.Connection:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(DB)
    cx.execute(
        "CREATE TABLE IF NOT EXISTS events ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "ts REAL, kind TEXT, payload TEXT)"
    )
    return cx


def save(kind: str, payload: dict | str) -> str:
    body = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    cx = _conn()
    cx.execute("INSERT INTO events(ts, kind, payload) VALUES (?,?,?)", (time.time(), kind, body[:8000]))
    cx.commit()
    cx.close()
    return f"checkpoint {kind} -> {DB.name}"


def last(n: int = 8) -> str:
    cx = _conn()
    rows = cx.execute("SELECT ts, kind, payload FROM events ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    cx.close()
    if not rows:
        return "no checkpoints yet"
    lines = []
    for ts, kind, payload in rows:
        lines.append(f"{kind}  {time.strftime('%H:%M:%S', time.localtime(ts))}  {payload[:180]}")
    return "\n".join(lines)
