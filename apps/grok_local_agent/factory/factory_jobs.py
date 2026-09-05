"""Persistent factory jobs. Resume after restart. Separate from lab jobs."""
from __future__ import annotations

import json
import time
import uuid

from ..checkpoint import _conn, save as ckpt

STATES = (
    "CREATED", "ANALYZING", "DESIGNING_DSP", "GENERATING_SPEC", "GENERATING_CODE",
    "GENERATING", "WAITING_PERMISSION", "BUILDING", "BUILD_FAILED",
    "VALIDATING", "VALIDATION_FAILED", "AUDIO_TESTING", "REGRESSION_TESTING",
    "PACKAGING", "RELEASE_CANDIDATE", "DONE", "FAILED", "ROLLED_BACK",
)

AVATAR = {
    "ANALYZING": "thinking",
    "DESIGNING_DSP": "thinking",
    "GENERATING": "working",
    "WAITING_PERMISSION": "warning",
    "BUILDING": "working",
    "BUILD_FAILED": "error",
    "VALIDATING": "working",
    "VALIDATION_FAILED": "error",
    "AUDIO_TESTING": "working",
    "PACKAGING": "working",
    "DONE": "success",
    "FAILED": "error",
    "ROLLED_BACK": "warning",
    "CREATED": "idle",
}


def _db():
    cx = _conn()
    cx.execute(
        "CREATE TABLE IF NOT EXISTS factory_jobs ("
        "id TEXT PRIMARY KEY, ts REAL, state TEXT, payload TEXT)"
    )
    return cx


def create(plugin_name: str, plugin_type: str = "utility", framework: str = "DPF", **extra) -> dict:
    job = {
        "job_id": uuid.uuid4().hex[:12],
        "plugin_name": plugin_name[:80],
        "plugin_type": plugin_type,
        "framework": framework,
        "created_at": time.time(),
        "updated_at": time.time(),
        "source_audio": extra.get("source_audio"),
        "target_description": extra.get("target_description", "probe"),
        "dsp_spec": extra.get("dsp_spec"),
        "parameters": extra.get("parameters"),
        "current_state": "CREATED",
        "starting_git_sha": extra.get("starting_git_sha"),
        "backup_ref": extra.get("backup_ref"),
        "build_directory": extra.get("build_directory"),
        "output_vst3": extra.get("output_vst3"),
        "validation_result": None,
        "test_result": None,
        "installer_path": None,
        "errors": [],
        "final_sha": None,
    }
    cx = _db()
    cx.execute(
        "INSERT OR REPLACE INTO factory_jobs(id, ts, state, payload) VALUES (?,?,?,?)",
        (job["job_id"], job["created_at"], job["current_state"], json.dumps(job, ensure_ascii=False)),
    )
    cx.commit()
    cx.close()
    ckpt("factory_job", job)
    _avatar(job["current_state"])
    return job


def set_state(job_id: str, state: str, **fields) -> dict:
    if state not in STATES:
        return {"ok": False, "error": "bad state", "states": list(STATES)}
    cx = _db()
    row = cx.execute("SELECT payload FROM factory_jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        cx.close()
        return {"ok": False, "error": "unknown job"}
    job = json.loads(row[0])
    job["current_state"] = state
    job["updated_at"] = time.time()
    for k, v in fields.items():
        if k == "errors" and isinstance(v, str):
            job.setdefault("errors", []).append(v)
        else:
            job[k] = v
    cx.execute(
        "INSERT OR REPLACE INTO factory_jobs(id, ts, state, payload) VALUES (?,?,?,?)",
        (job["job_id"], job["updated_at"], job["current_state"], json.dumps(job, ensure_ascii=False)),
    )
    cx.commit()
    cx.close()
    ckpt("factory_job", {"id": job_id, "state": state})
    _avatar(state)
    return {"ok": True, **job}


def get(job_id: str) -> dict | None:
    cx = _db()
    row = cx.execute("SELECT payload FROM factory_jobs WHERE id=?", (job_id,)).fetchone()
    cx.close()
    return json.loads(row[0]) if row else None


def latest() -> dict | None:
    cx = _db()
    row = cx.execute("SELECT payload FROM factory_jobs ORDER BY ts DESC LIMIT 1").fetchone()
    cx.close()
    return json.loads(row[0]) if row else None


def _avatar(state: str) -> None:
    try:
        from ..avatar.avatar_state import set_state
        set_state(AVATAR.get(state, "idle"), "factory " + state)
    except Exception:
        pass
