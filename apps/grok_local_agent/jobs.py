"""Job memory so Thall work survives restart."""
from __future__ import annotations

import json
import time
import uuid

from .checkpoint import _conn, save as ckpt

STAGES = ("start", "analyze", "design", "build", "test", "confirm", "done")


def create(title: str, notes: str = "") -> dict:
    job = {
        "id": uuid.uuid4().hex[:10],
        "title": title[:120] or "untitled",
        "stage": "start",
        "notes": notes[:500],
        "ts": time.time(),
    }
    ckpt("job", job)
    cx = _conn()
    cx.execute(
        "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, ts REAL, stage TEXT, payload TEXT)"
    )
    cx.execute(
        "INSERT OR REPLACE INTO jobs(id, ts, stage, payload) VALUES (?,?,?,?)",
        (job["id"], job["ts"], job["stage"], json.dumps(job, ensure_ascii=False)),
    )
    cx.commit()
    cx.close()
    return job


def update(job_id: str, stage: str | None = None, notes: str | None = None) -> dict:
    cx = _conn()
    cx.execute(
        "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, ts REAL, stage TEXT, payload TEXT)"
    )
    row = cx.execute("SELECT payload FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        cx.close()
        return {"ok": False, "error": "unknown job"}
    job = json.loads(row[0])
    if stage:
        if stage not in STAGES:
            cx.close()
            return {"ok": False, "error": "bad stage", "stages": list(STAGES)}
        job["stage"] = stage
    if notes is not None:
        job["notes"] = notes[:500]
    job["ts"] = time.time()
    cx.execute(
        "INSERT OR REPLACE INTO jobs(id, ts, stage, payload) VALUES (?,?,?,?)",
        (job["id"], job["ts"], job["stage"], json.dumps(job, ensure_ascii=False)),
    )
    cx.commit()
    cx.close()
    ckpt("job", job)
    return {"ok": True, **job}


def current() -> dict:
    cx = _conn()
    cx.execute(
        "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, ts REAL, stage TEXT, payload TEXT)"
    )
    rows = cx.execute("SELECT payload FROM jobs ORDER BY ts DESC LIMIT 5").fetchall()
    cx.close()
    jobs = [json.loads(r[0]) for r in rows]
    return {"ok": True, "jobs": jobs, "stages": list(STAGES)}
