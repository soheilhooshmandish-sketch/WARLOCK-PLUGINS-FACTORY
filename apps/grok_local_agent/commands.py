"""Short commands. Still go through permissions."""
from __future__ import annotations

from .backup_gate import snapshot
from .health import report as health
from .jobs import current as jobs
from .killswitch import halt, resume
from .operator import status as op_status


def handle(text: str) -> dict | None:
    key = (text or "").strip().lower()
    key = key.replace("farnaz,", "").replace("فرناز،", "").replace("فرناز ", "").strip()
    if key in {"status", "وضعیت"}:
        return {"ok": True, "cmd": "status", "health": health(), "operator": op_status(), "jobs": jobs()}
    if key in {"backup", "بکاپ"}:
        return {"ok": True, "cmd": "backup", **snapshot("command")}
    if key in {"stop", "بایست"}:
        return {"ok": True, "cmd": "stop", **halt("command")}
    if key in {"resume", "ادامه"}:
        return {"ok": True, "cmd": "resume", **resume()}
    if key in {"dnd", "سکوت"}:
        from .dnd import enable
        return enable("command")
    return None
