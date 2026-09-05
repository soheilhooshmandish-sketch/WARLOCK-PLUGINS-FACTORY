"""farnaz doctor — inspect, do not repair without permission."""
from __future__ import annotations

import shutil
from pathlib import Path

from ..config import PROJECT_ROOT, PROTECTED_PATHS, STATE_DIR, STATIC_DIR
from ..killswitch import halted
from .toolchain import detect


def _disk() -> dict:
    usage = shutil.disk_usage(str(PROJECT_ROOT))
    free_gb = usage.free / (1024 ** 3)
    status = "HEALTHY" if free_gb > 1 else "FAILED" if free_gb < 0.2 else "WARNING"
    return {"status": status, "free_gb": round(free_gb, 2)}


def report() -> dict:
    tools = detect()
    missing = tools["missing_required"]
    db = STATE_DIR / "farnaz.db"
    avatar = STATIC_DIR / "desktop.html"
    local_agent = PROJECT_ROOT / "apps" / "local_agent"
    parts = {
        "git": "HEALTHY" if shutil.which("git") else "FAILED",
        "database": "HEALTHY" if db.exists() or STATE_DIR.exists() else "WARNING",
        "avatar": "HEALTHY" if avatar.exists() else "FAILED",
        "chatgpt_agent_present": "HEALTHY" if local_agent.exists() else "FAILED",
        "protected": "HEALTHY" if "apps/local_agent" in PROTECTED_PATHS else "FAILED",
        "killswitch": "WARNING" if halted() else "HEALTHY",
        "disk": _disk()["status"],
        "toolchain": "FAILED" if missing else "HEALTHY",
        "dpf": "FAILED" if tools["tools"]["dpf"]["status"] != "available" else "HEALTHY",
        "pluginval": "FAILED" if tools["tools"]["pluginval"]["status"] != "available" else "HEALTHY",
        "nsis": "FAILED" if tools["tools"]["nsis"]["status"] != "available" else "HEALTHY",
    }
    overall = "HEALTHY"
    if any(v == "FAILED" for v in parts.values()):
        overall = "FAILED"
    elif any(v == "WARNING" for v in parts.values()):
        overall = "WARNING"
    return {
        "ok": overall != "FAILED",
        "status": overall,
        "parts": parts,
        "missing_required": missing,
        "disk": _disk(),
        "note": "FAILED toolchain is expected until CMake/Clang/DPF/pluginval/NSIS are installed with permission.",
    }
