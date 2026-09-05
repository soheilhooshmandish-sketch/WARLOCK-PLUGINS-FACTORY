"""Backup → change → test → commit. Farnaz may not destroy a healthy tree."""
from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .config import PROJECT_ROOT, STATE_DIR


def _git(*args: str) -> str:
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        return str(exc)
    return ((r.stdout or "") + (r.stderr or "")).strip()[:2000]


def snapshot(reason: str = "manual") -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    head = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest = STATE_DIR / "backups"
    dest.mkdir(exist_ok=True)
    patch = dest / f"{stamp}.diff"
    if status:
        diff = _git("diff")
        patch.write_text(diff or status, encoding="utf-8")
    return {
        "ok": True,
        "reason": reason,
        "head": head[:40],
        "dirty": bool(status),
        "patch": str(patch) if status else None,
        "law": "Backup → change → test → commit. Rollback = git checkout HEAD -- <file> or apply patch.",
    }
